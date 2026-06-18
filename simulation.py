"""The engine -- lap times, qualifying (with the 107% rule), races, incidents,
damage, and DNFs.

Damage is not one faceless number. An incident has a CAUSE and a SEVERITY
(minor/moderate/major), and it does specific harm to specific systems -- AERO and
SUSPENSION -- each of which taxes every remaining lap. Carried damage also quietly
raises the chance of a later failure, so a small early knock can end a race many
laps on. Major hits can retire a car outright (DNF).

Causes split into SOLO events (running wide, a sausage kerb, the wall) that hurt
one car, and CONTACT -- a two-car collision off a failed overtake. A collision
damages BOTH cars (the car defending takes a smaller share of a glancing blow, a
full share of a big shunt), and a major hit can retire either or both of them.

Qualifying enforces Formula 1's real 107% rule: lap outside 107% of pole and you
do not make the race. Nobody is excluded by name -- the standard does the work.

Tyres are the strategic layer. Wear is a per-lap time penalty that grows with the
stint (the same shape as damage), scaled by the COMPOUND fitted (soft/medium/hard
trade grip against durability), the track's abrasiveness, and the driver's tyre
management, and it RESETS in the pits at the cost of a fixed time loss. Before the
race each car commits to a PLAN -- compounds and pit laps -- chosen by
_plan_strategy: the cheapest sensible 1- or 2-stop using at least two compounds
(F1's rule), as judged through the haze of the driver's `strategy` rating. A poor
strategist misjudges the plan and picks a worse one; a master nails the optimum.
"""

import random
from dataclasses import dataclass, field

from drivers import Driver


# --- Pace / overtaking knobs -------------------------------------------------
# DIRTY_AIR_GAP and HELD_UP_GAP stay in ABSOLUTE seconds on purpose -- "within a
# second" and "0.7s behind" are real, track-independent racing distances (think
# DRS range), not fractions of a lap.
DIRTY_AIR_GAP = 1.0
HELD_UP_GAP = 0.7
PASS_CLEAR_GAP = 0.05          # margin a completed pass emerges ahead by, so it sticks
BASE_PASS_CHANCE = 0.30
PACE_WEIGHT = 0.6
RACECRAFT_WEIGHT = 0.25
BASE_FLOOR = 0.03              # floor pass chance on an easy track; tightens hard as difficulty rises

QUALIFYING_CUTOFF = 1.07        # 107% rule: slower than this multiple of pole = DNQ
RACECRAFT_FLOOR = 0.05          # at/below this, a driver is hopeless: a guaranteed race-ending error

# --- Incident / attrition knobs (mistake chances scale with 1 - racecraft) ---
# Tuned to modern-F1 attrition over a 40-lap race: among the 18 genuine
# competitors, ~1.7 retirements per race (~9.6%), ~16% of races clean. (The two
# Objectivism cars are guaranteed to retire on top of that -- see RACECRAFT_FLOOR.)
SOLO_MISTAKE_CHANCE = 0.017     # lone error per lap, before skill-scaling
CONTACT_CHANCE = 0.045          # chance a failed move turns into contact, before skill-scaling
MAJOR_DNF_CHANCE = 0.60         # chance a 'major' SOLO incident ends the race on the spot
DAMAGE_FAILURE_FACTOR = 0.008   # per-lap DNF risk per 1.0s/lap of carried damage
SEVERITY_SPLIT = (0.58, 0.23)   # P(minor), P(moderate); remainder is major
SEVERITY_MULT = {"minor": 1.0, "moderate": 2.2, "major": 4.5}

# The per-lap chances above were calibrated against a 40-lap race. Real circuits
# run anywhere from 44 (Spa) to 78 (Monaco) laps, so we scale the per-lap rates by
# BASELINE_LAPS / laps to keep expected attrition PER RACE roughly constant.
# Length then stops inflating the carnage, and the TRACK (its overtaking
# difficulty) becomes what actually makes one circuit messier than another.
BASELINE_LAPS = 40

# A driver's `pace` is an abstract ~90s figure -- skill, not a real lap time. To
# get realistic times we scale it to each track: a notional REFERENCE_PACE driver
# laps in exactly the track's base_lap_time. PACE and CONSISTENCY scale (they ARE
# the lap); car-to-car gaps, one-off time losses, and carried damage stay in real
# seconds (a 1s gap is 1s anywhere -- it's a distance-in-time, not a lap).
REFERENCE_PACE = 90.0

# --- The standing start ------------------------------------------------------
# At lights-out the CLOCK hasn't started -- GRID POSITION is the only truth. The
# start is its own phase: we string the field out by grid (each slot a little
# further back in race time), then let a LAUNCH -- the driver's launch skill plus
# pure chaos -- shuffle the pack on the run to the first corner. This seeds
# total_time with a real spread so that from lap 1 the engine knows who is where,
# instead of trying to order twenty cars that all read 0.0 (which scrambled the
# old lap 1).
GRID_INTERVAL = 0.45    # race-time between consecutive grid slots as the field strings out
LAUNCH_SPREAD = 0.35    # the chaos of the getaway (gaussian sigma, in seconds)
LAUNCH_SKILL = 0.5      # how much racecraft helps (or, when low, hurts) off the line

# Collisions take two. A big (major) hit can pitch either car out -- and rolling
# it for each independently means a really big one sometimes takes BOTH. The car
# defending takes a smaller share of a glancing blow, but a major shunt wrecks both.
COLLISION_DNF_CHANCE = 0.42     # per-car DNF chance in a MAJOR collision
DEFENDER_SHARE = {"minor": 0.4, "moderate": 0.6, "major": 1.0}  # damage the passed car absorbs

# --- Tyres ------------------------------------------------------------------
# Wear is the SAME machine as damage -- a per-lap time penalty that grows -- but
# pointed at a different cause and, crucially, a different CURE. Damage comes from
# random incidents and never heals; wear comes from just driving (predictable,
# continuous) and RESETS in the pits. The pit stop costs a fixed chunk of time,
# and deciding when that cost is worth paying is where strategy is born.
#
# The penalty is a function of STINT LENGTH (laps on the current set): a linear
# bleed plus a small quadratic 'cliff' as the tyre gives up late in a stint. Two
# dials scale it: the TRACK's abrasiveness (tracks.tyre_wear) and the DRIVER's
# tyre_management (a high manager wears more slowly). We don't model graining or
# core temps -- tyre_management IS our abstraction for "keeps them in the window".
TYRE_LINEAR = 0.058     # seconds/lap added per lap of stint (the steady bleed)
TYRE_QUAD = 0.0016      # the late 'cliff': grows with stint length squared
TYRE_MGMT_SWING = 0.7   # how far tyre_management swings the wear rate (+/- ~0.35x)
PIT_LOSS = 23.0         # time lost for a stop (pit lane + stationary), absolute seconds

# --- Compounds & strategy ----------------------------------------------------
# A compound is just two dials on the wear machine we already built: GRIP (a flat
# per-lap time offset -- soft is quicker) and WEAR (a multiplier on how fast the
# penalty grows -- soft dies sooner). The trade is the whole game: soft wins short
# stints, hard wins long ones, medium splits the difference. F1's two-compound
# rule (you must run at least two types in a dry race) is what forces a PLAN
# rather than just bolting on the single fastest tyre -- so the planner always
# builds plans that use >= 2 compounds, which also guarantees at least one stop.
STRATEGY_MAX_STOPS = 2   # plans considered run 1 or 2 stops (a 3-stop is a one-line extension)
STRATEGY_NOISE = 14.0    # seconds of plan-cost MISJUDGEMENT a hopeless strategist suffers
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Compound:
    name: str
    grip: float          # flat per-lap time offset in seconds (negative = faster)
    wear: float          # multiplier on the wear rate (>1 wears faster)


# The three dry tyres. Tuned so each is the fastest choice for SOME stint length:
# soft ~1-15 laps, medium ~16-23, hard ~24+ (before track/management scaling).
SOFT = Compound("soft", -0.75, 2.1)
MEDIUM = Compound("medium", -0.05, 1.0)
HARD = Compound("hard", 0.50, 0.5)
COMPOUNDS = [SOFT, MEDIUM, HARD]


@dataclass
class RacePlan:
    """A pre-race strategy: the compound for each stint and the laps to pit on.
    compounds has one more entry than pit_laps (the stint after the final stop)."""
    compounds: list      # list[Compound], one per stint
    pit_laps: list        # list[int], the lap each stop is taken on (ascending)


@dataclass
class CarState:
    driver: Driver
    grid_position: int = 0
    total_time: float = 0.0
    last_lap: float = 0.0
    aero_damage: float = 0.0          # persistent per-lap penalty: bodywork/wing
    suspension_damage: float = 0.0    # persistent per-lap penalty: mechanical
    retired: bool = False
    retired_on_lap: int = 0
    doomed_lap: int = 0               # >0 if hopeless racecraft has marked a guaranteed DNF lap
    stint_laps: int = 0               # laps on the current set of tyres -- resets at a pit stop
    pit_count: int = 0                # how many stops made so far
    compound: Compound = MEDIUM       # the tyre currently fitted
    plan: RacePlan = None             # the pre-race strategy, assigned by _plan_strategy before lights-out

    @property
    def damage(self):
        return self.aero_damage + self.suspension_damage


@dataclass
class Standing:
    position: int
    name: str
    team: str
    grid_position: int
    total_time: float
    last_lap: float
    gap_to_leader: float
    aero_damage: float
    suspension_damage: float
    retired: bool
    retired_on_lap: int
    stint_laps: int = 0          # laps on the current tyres -- for the timing tower
    compound: str = ""           # the tyre currently fitted

    @property
    def damage(self):
        return self.aero_damage + self.suspension_damage

    @classmethod
    def from_car(cls, car, position, gap_to_leader):
        """Snapshot a live CarState into a Standing. Keyword args on purpose: add a
        field to the car and you thread it through HERE, in one place, instead of a
        fragile positional constructor buried in _standings()."""
        return cls(
            position=position,
            name=car.driver.name,
            team=car.driver.team,
            grid_position=car.grid_position,
            total_time=car.total_time,
            last_lap=car.last_lap,
            gap_to_leader=gap_to_leader,
            aero_damage=car.aero_damage,
            suspension_damage=car.suspension_damage,
            retired=car.retired,
            retired_on_lap=car.retired_on_lap,
            stint_laps=car.stint_laps,
            compound=car.compound.name,
        )


@dataclass
class Incident:
    driver_name: str
    lap: int
    cause: str           # "collision" | "wall" | "kerb" | "off-track" | "damage failure" | "over the limit"
    severity: str        # "minor" | "moderate" | "major"
    time_lost: float
    aero_added: float
    suspension_added: float
    retirement: bool
    other_name: str = ""        # the other car in a collision ("" for solo incidents)
    other_retired: bool = False # did the OTHER car retire in this collision
    location: str = ""          # named corner where it happened ("" if track-agnostic)


@dataclass
class Overtake:
    """A clean, completed pass -- the OTHER half of the racing story. Recorded so
    the commentary has something to call; whether a given pass is worth a mention
    is left to the display layer (a pass for the lead matters; P14 rarely does)."""
    passer: str
    passed: str
    lap: int
    position: int        # the place being fought for (1 = the lead)
    location: str = ""   # named overtaking corner ("" if track-agnostic); "the start" for getaways
    places_gained: int = 0   # only meaningful for a start: places made up off the line


@dataclass
class PitStop:
    """A trip down the pit lane: fresh tyres at the cost of track time. The other
    new thread the commentary can pull on -- a stop reshuffles the race."""
    driver_name: str
    lap: int
    stop_number: int     # 1 = first stop of the race for this car
    old_stint: int       # how many laps the tyres being changed had done
    compound: str = ""   # the fresh compound now fitted


@dataclass
class LapReport:
    lap: int
    standings: list = field(default_factory=list)   # list[Standing]
    incidents: list = field(default_factory=list)   # list[Incident]
    overtakes: list = field(default_factory=list)   # list[Overtake]
    pit_stops: list = field(default_factory=list)   # list[PitStop]


def simulate_lap(driver, track):
    """One lap in seconds: the abstract pace scaled to the track's real lap time
    (pace and consistency scale together, so a steadier driver stays steadier)."""
    raw = driver.pace + random.gauss(0, driver.consistency)
    return raw * (track.base_lap_time / REFERENCE_PACE)


def run_qualifying(grid, track):
    """Each driver sets one flying lap. Apply the 107% rule.

    Returns a list of (driver, lap, qualified) sorted fastest first. A driver is
    'qualified' only if their lap is within 107% of pole. (The cutoff is relative,
    so track scaling shifts every time together and never changes who qualifies.)
    """
    results = [(driver, simulate_lap(driver, track)) for driver in grid]
    results.sort(key=lambda pair: pair[1])
    cutoff = results[0][1] * QUALIFYING_CUTOFF
    return [(driver, lap, lap <= cutoff) for driver, lap in results]


def attempt_overtake(chaser, defender, difficulty):
    pace_advantage = defender.driver.pace - chaser.driver.pace
    skill_advantage = chaser.driver.racecraft - defender.driver.racecraft
    # A faster, craftier driver is likelier to get the move done -- but a hard
    # track DAMPS how much of that edge you can actually use. At Monaco there's
    # nowhere to put the car however quick you are, so the advantage counts for
    # little; at Monza it counts for nearly all of itself.
    edge = (pace_advantage * PACE_WEIGHT
            + skill_advantage * RACECRAFT_WEIGHT) * (1 - difficulty)
    chance = BASE_PASS_CHANCE - difficulty + edge
    # The floor tightens with difficulty too: evenly-matched cars almost never
    # clear each other at a fortress, so a train stays a train for lap after lap.
    floor = BASE_FLOOR * (1 - difficulty) ** 2
    return random.random() < max(floor, min(0.95, chance))


def _roll_severity():
    r = random.random()
    minor_p, moderate_p = SEVERITY_SPLIT
    if r < minor_p:
        return "minor"
    if r < minor_p + moderate_p:
        return "moderate"
    return "major"


def _solo_cause():
    r = random.random()
    if r < 0.50:
        return "off-track"
    if r < 0.85:
        return "kerb"
    return "wall"


def _make_incident(car, lap, cause):
    """Build a SOLO incident (off-track, kerb, wall), apply lasting damage, decide DNF.

    An off-track mostly costs time now; kerbs and walls mostly cost lasting damage
    (suspension and aero) that taxes every future lap. Contact between cars is a
    two-car event handled by _collide.
    """
    severity = _roll_severity()
    mult = SEVERITY_MULT[severity]
    time_lost = aero = susp = 0.0

    if cause == "off-track":
        time_lost = random.uniform(1.0, 3.0) * mult
        if severity != "minor":
            aero = random.uniform(0.0, 0.15) * mult
    elif cause == "kerb":
        time_lost = random.uniform(0.3, 1.0) * mult
        susp = random.uniform(0.10, 0.30) * mult        # kerbs batter the suspension
        aero = random.uniform(0.0, 0.10) * mult
    elif cause == "wall":
        time_lost = random.uniform(1.5, 3.5) * mult
        aero = random.uniform(0.15, 0.35) * mult
        susp = random.uniform(0.10, 0.30) * mult

    car.aero_damage += aero
    car.suspension_damage += susp

    retirement = (severity == "major" and random.random() < MAJOR_DNF_CHANCE)
    return Incident(car.driver.name, lap, cause, severity,
                    time_lost, aero, susp, retirement)


def _collide(chaser, defender, lap):
    """A failed move turns into CONTACT -- a two-car event.

    Both cars take damage; the chaser (who threw the move) takes the full share,
    the defender a smaller one (scaled up to a full share for a major shunt). A
    major hit rolls a DNF for each car independently, so a really big one can take
    the chaser, the defender, or both. The defender is wounded retroactively: time
    and damage are added to a car already processed this lap, which the end-of-lap
    standings pick up.

    Returns (incident, chaser_time_lost, chaser_retired).
    """
    severity = _roll_severity()
    mult = SEVERITY_MULT[severity]

    def harm(bias):
        return (random.uniform(0.5, 2.0) * mult * bias,    # time lost
                random.uniform(0.10, 0.30) * mult * bias,  # aero
                random.uniform(0.05, 0.20) * mult * bias)  # suspension

    c_time, c_aero, c_susp = harm(1.0)
    d_time, d_aero, d_susp = harm(DEFENDER_SHARE[severity])

    chaser.aero_damage += c_aero
    chaser.suspension_damage += c_susp
    defender.aero_damage += d_aero
    defender.suspension_damage += d_susp
    defender.total_time += d_time              # the passed car loses time too

    chaser_out = defender_out = False
    if severity == "major":
        chaser_out = random.random() < COLLISION_DNF_CHANCE
        defender_out = random.random() < COLLISION_DNF_CHANCE

    if defender_out and not defender.retired:
        defender.retired, defender.retired_on_lap = True, lap

    inc = Incident(chaser.driver.name, lap, "collision", severity,
                   c_time, c_aero, c_susp, chaser_out,
                   other_name=defender.driver.name, other_retired=defender_out)
    return inc, c_time, chaser_out


def _standings(cars):
    """Running cars first (by race time), then retirements (latest DNF placed higher)."""
    active = sorted((c for c in cars if not c.retired), key=lambda c: c.total_time)
    retired = sorted((c for c in cars if c.retired), key=lambda c: -c.retired_on_lap)
    leader_time = active[0].total_time if active else 0.0
    ordered = active + retired
    return [Standing.from_car(c, pos, c.total_time - leader_time)
            for pos, c in enumerate(ordered, start=1)]


def _retire(car, lap, old_total, lap_time, time_lost):
    car.retired, car.retired_on_lap = True, lap
    car.total_time = old_total + lap_time + time_lost
    car.last_lap = car.total_time - old_total


def _pick_corner(track, overtaking=False):
    """Where did it happen? Passing moves favour the track's overtaking spots;
    solo errors can happen anywhere. Returns "" only if the track has no corners."""
    if not track.corners:
        return ""
    pool = [c.name for c in track.corners if c.overtaking] if overtaking else []
    if not pool:                                   # no OT corners, or a solo error
        pool = [c.name for c in track.corners]
    return random.choice(pool)


def _run_start(cars):
    """Resolve the standing start, returning the position changes off the line.

    Grid position is the only truth at lights-out -- the clock reads zero for
    everyone -- so we seed each car's race time from where it starts (each slot a
    little further back), then let a launch shuffle the pack: racecraft helps, but
    chaos has the final say. A great getaway eats into your deficit; a bog-down
    hands places away. The resulting spread is what lets the engine know who is
    ahead of whom from the very first lap.

    Returns the cars that gained places as Overtake events, for the commentary.
    """
    for car in cars:
        base = (car.grid_position - 1) * GRID_INTERVAL
        jitter = random.gauss(0, LAUNCH_SPREAD)
        skill = (car.driver.launch - 0.5) * LAUNCH_SKILL      # >0 gains, <0 loses
        car.total_time = max(0.0, base + jitter - skill)

    order = sorted(cars, key=lambda c: c.total_time)
    events = []
    for new_pos, car in enumerate(order, start=1):
        gained = car.grid_position - new_pos
        if gained > 0:
            events.append(Overtake(car.driver.name, "", lap=1, position=new_pos,
                                   location="the start", places_gained=gained))
    return events


def _tyre_penalty(car, track):
    """The per-lap time cost of the current tyres, as a function of stint length.

    A steady linear bleed plus a small quadratic 'cliff' late in the stint, scaled
    by the COMPOUND's wear rate, the track's abrasiveness, and softened by the
    driver's tyre management. This is the wear equivalent of `car.damage`: a number
    that taxes the lap and that a pit stop wipes back to zero.
    """
    s = car.stint_laps
    penalty = TYRE_LINEAR * s + TYRE_QUAD * s * s
    penalty *= car.compound.wear                            # soft wears fast, hard slow
    penalty *= track.tyre_wear                              # abrasive tracks chew tyres
    penalty *= 1.0 - (car.driver.tire_management - 0.5) * TYRE_MGMT_SWING
    return max(0.0, penalty)


def _plan_strategy(driver, track, laps):
    """Build a race plan before the lights go out: which compound for each stint,
    and which laps to pit on.

    We enumerate every sensible structure -- a 1-stop or 2-stop, using at least two
    compounds (the rule) -- cost each one with the SAME wear maths the race itself
    uses, optimise the lap-split within each, and keep the cheapest of each. Then
    the driver's `strategy` rating clouds the final choice: a poor strategist
    misjudges the plan costs (gaussian noise that shrinks as strategy rises) and
    can talk themselves into a worse plan -- the wrong number of stops, the wrong
    rubber. A master like Machiavelli almost always lands on the true optimum.
    """
    # This driver's effective wear scaling at this track (management + abrasiveness).
    w = track.tyre_wear * (1.0 - (driver.tire_management - 0.5) * TYRE_MGMT_SWING)

    # Precompute the cost of running each compound for n laps (variable time only:
    # grip + wear; the constant base lap is identical across plans, so it drops out).
    cost = {}
    for c in COMPOUNDS:
        arr = [0.0] * (laps + 1)
        for n in range(1, laps + 1):
            sum_s = n * (n + 1) / 2
            sum_s2 = n * (n + 1) * (2 * n + 1) / 6
            arr[n] = c.grip * n + c.wear * w * (TYRE_LINEAR * sum_s + TYRE_QUAD * sum_s2)
        cost[c.name] = arr

    structures = []   # (best_cost, RacePlan)

    # One-stop: two distinct compounds; scan where to split the race.
    for c1 in COMPOUNDS:
        for c2 in COMPOUNDS:
            if c1 is c2:
                continue
            best = None
            for a in range(1, laps):
                total = cost[c1.name][a] + cost[c2.name][laps - a] + PIT_LOSS
                if best is None or total < best[0]:
                    best = (total, [a])
            structures.append((best[0], RacePlan([c1, c2], best[1])))

    # Two-stop: any three stints using >= 2 distinct compounds; scan both splits.
    if STRATEGY_MAX_STOPS >= 2:
        for c1 in COMPOUNDS:
            for c2 in COMPOUNDS:
                for c3 in COMPOUNDS:
                    if len({c1.name, c2.name, c3.name}) < 2:
                        continue
                    best = None
                    for a in range(1, laps - 1):
                        ca = cost[c1.name][a]
                        for b in range(a + 1, laps):
                            total = ca + cost[c2.name][b - a] + cost[c3.name][laps - b] + 2 * PIT_LOSS
                            if best is None or total < best[0]:
                                best = (total, [a, b])
                    structures.append((best[0], RacePlan([c1, c2, c3], best[1])))

    # The skill: misjudge the costs, then pick what LOOKS cheapest.
    noise = STRATEGY_NOISE * (1.0 - driver.strategy)
    chosen = min(structures, key=lambda cp: cp[0] + (random.gauss(0, noise) if noise else 0.0))
    return chosen[1]


def run_race(starting_grid, track, laps=None, difficulty=None):
    # The track supplies the race distance and how hard it is to pass; either can
    # still be overridden by hand (handy for testing).
    if laps is None:
        laps = track.laps
    if difficulty is None:
        difficulty = track.overtaking_difficulty

    # Keep per-race attrition steady regardless of how long the race is.
    length_scale = BASELINE_LAPS / laps

    cars = [CarState(driver, grid_position=i + 1)
            for i, driver in enumerate(starting_grid)]

    # Hopeless racecraft is a sentence, not a tendency: pick the lap on which the
    # inevitable race-ending mistake arrives. (They still flail their way there.)
    for car in cars:
        if car.driver.racecraft <= RACECRAFT_FLOOR:
            car.doomed_lap = random.randint(1, laps)

    # Pre-race strategy: each car commits to a plan (compounds + pit laps) and bolts
    # on its starting tyre before the lights go out.
    for car in cars:
        car.plan = _plan_strategy(car.driver, track, laps)
        car.compound = car.plan.compounds[0]

    history = []

    # Resolve the standing start: this seeds each car's total_time with a real
    # grid-based spread, so the clock and track position now mean distinct things
    # and the lap loop below knows who is where from lap 1 onward.
    start_events = _run_start(cars)

    for lap in range(1, laps + 1):
        running = sorted((c for c in cars if not c.retired), key=lambda c: c.total_time)
        incidents = []
        overtakes = list(start_events) if lap == 1 else []
        pit_stops = []

        for i, car in enumerate(running):
            car.stint_laps += 1                                       # another lap on this set
            old_total = car.total_time
            tyre = _tyre_penalty(car, track)
            grip = car.compound.grip
            lap_time = simulate_lap(car.driver, track) + car.damage + tyre + grip  # damage AND tyres tax the lap
            time_lost = 0.0

            # 0. Hopeless racecraft: the inevitable, race-ending error finally arrives
            if car.doomed_lap and lap >= car.doomed_lap:
                car.retired, car.retired_on_lap = True, lap
                incidents.append(Incident(car.driver.name, lap, "over the limit",
                                          "major", 0.0, 0.0, 0.0, True,
                                          location=_pick_corner(track)))
                continue

            # 1. Delayed failure: carried damage can finally let go, laps later
            if car.damage > 0 and random.random() < DAMAGE_FAILURE_FACTOR * length_scale * car.damage:
                car.retired, car.retired_on_lap = True, lap
                incidents.append(Incident(car.driver.name, lap, "damage failure",
                                          "major", 0.0, 0.0, 0.0, True))
                continue

            # 2. Solo mistake: a lone error, far likelier for low-racecraft drivers
            if random.random() < SOLO_MISTAKE_CHANCE * length_scale * (1 - car.driver.racecraft):
                inc = _make_incident(car, lap, _solo_cause())
                inc.location = _pick_corner(track)
                incidents.append(inc)
                time_lost += inc.time_lost
                if inc.retirement:
                    _retire(car, lap, old_total, lap_time, time_lost)
                    continue

            # 2b. Pit stop -- driven by the PLAN, not a reactive threshold. If this
            # lap is the next scheduled stop, box: fit the planned compound, reset
            # the tyres, eat the pit loss. The plan was built pre-race by
            # _plan_strategy; how good it is depends on the driver's `strategy`.
            if (car.pit_count < len(car.plan.pit_laps)
                    and lap == car.plan.pit_laps[car.pit_count]):
                old_stint = car.stint_laps
                car.pit_count += 1
                car.compound = car.plan.compounds[car.pit_count]      # the fresh rubber
                car.stint_laps = 0
                time_lost += PIT_LOSS
                pit_stops.append(PitStop(car.driver.name, lap, car.pit_count,
                                         old_stint, car.compound.name))
                car.total_time = old_total + lap_time + time_lost
                car.last_lap = car.total_time - old_total
                continue                                              # the in-lap skips the on-track fight

            # 3. The leader runs in clear air
            if i == 0:
                car.total_time = old_total + lap_time + time_lost
                car.last_lap = car.total_time - old_total
                continue

            # 4. Everyone else may catch the car ahead and try a move
            ahead = running[i - 1]
            provisional = old_total + lap_time + time_lost

            if ahead.retired or provisional >= ahead.total_time + DIRTY_AIR_GAP:
                # Clear track ahead -- or the car ahead has already crashed out -- run own pace
                car.total_time = provisional
            elif attempt_overtake(car, ahead, difficulty):
                # A completed pass means emerging AHEAD of the car you passed. If
                # the chaser's own pace already does that (provisional below the
                # car ahead), keep it; otherwise nudge them just in front so the
                # pass STICKS in the running order. Without this, a car caught in
                # dirty air "passes" every single lap without ever getting by --
                # a phantom the commentary would dutifully (and wrongly) call.
                car.total_time = min(provisional, ahead.total_time - PASS_CLEAR_GAP)
                overtakes.append(Overtake(car.driver.name, ahead.driver.name, lap,
                                          position=i,
                                          location=_pick_corner(track, overtaking=True)))
            else:
                # The move didn't come off -- risk of contact, worse if clumsy
                if random.random() < CONTACT_CHANCE * length_scale * (1 - car.driver.racecraft):
                    inc, lost, chaser_out = _collide(car, ahead, lap)
                    inc.location = _pick_corner(track, overtaking=True)
                    incidents.append(inc)
                    time_lost += lost
                    if chaser_out:
                        _retire(car, lap, old_total, lap_time, time_lost)
                        continue
                    if ahead.retired:
                        car.total_time = old_total + lap_time + time_lost   # knocked them out -- road clear
                    else:
                        car.total_time = ahead.total_time + HELD_UP_GAP + time_lost
                else:
                    car.total_time = ahead.total_time + HELD_UP_GAP + time_lost

            car.last_lap = car.total_time - old_total

        history.append(LapReport(lap, _standings(cars), incidents, overtakes, pit_stops))

    return history


# --- Post-race analysis ------------------------------------------------------
# This reads the finished `history` and distils the story out of it. It is
# ANALYSIS, not presentation: it returns facts (names, laps, causes), and the
# display layer decides the words. The same "scan the frames, pull out events"
# move is what the live commentary engine will be built on.

@dataclass
class RaceSummary:
    circuit: str               # where the race was held ("" if unknown)
    total_laps: int
    starters: int
    finishers: int
    winner: str
    team: str
    winner_from: int           # grid position the winner started from
    pole_sitter: str
    podium: list               # [(position, name, team)]
    drive_of_the_day: tuple    # (name, places_gained) or None
    lead_changes: int
    fastest_lap_driver: str
    fastest_lap_time: float
    retirements: list          # [(name, lap, cause, location)] -- words live in display
    double_dnfs: list          # [(chaser, defender, lap, location)] from major collisions
    overtakes_count: int = 0   # clean on-track passes for position across the race


# A "flying lap" worth calling the fastest is one close to the track's clean lap.
# Defining the band RELATIVE to base_lap_time is the whole point: a fixed seconds
# window broke the moment lap times started scaling per circuit (Spa's ~105s laps
# fell off the top, Monaco's ~73s off the bottom). Pit in-laps (+PIT_LOSS) and
# incident laps land well outside this band, so the quickest in-band lap is real.
FASTLAP_MIN = 0.90      # nothing genuine is quicker than 90% of a clean lap
FASTLAP_MAX = 1.12      # slower than this is traffic or a stop, not a flyer


def summarize_race(history, track):
    """Distil a finished race `history` into a RaceSummary of key facts."""
    final = history[-1].standings
    total_laps = len(history)
    starters = len(final)
    runners = [s for s in final if not s.retired]
    finishers = len(runners)

    winner = runners[0] if runners else None
    pole = next((s for s in final if s.grid_position == 1), None)
    podium = [(s.position, s.name, s.team) for s in runners[:3]]

    # Drive of the day: most places gained among the finishers.
    dotd, best_gain = None, 0
    for s in runners:
        gain = s.grid_position - s.position
        if gain > best_gain:
            best_gain, dotd = gain, (s.name, gain)

    # Lead changes: walk the per-lap leader, seeded from the pole-sitter.
    lead_changes = 0
    prev_leader = pole.name if pole else None
    for rep in history:
        leader = rep.standings[0].name if rep.standings else None
        if leader and leader != prev_leader:
            lead_changes += 1
            prev_leader = leader

    # Fastest lap. APPROXIMATE: the engine folds traffic (dirty air, being held
    # up) into last_lap, so this is the best clean-ish lap seen, not a true
    # isolated flyer. A proper version means recording each car's raw pace lap
    # separately in run_race -- a good, well-contained future tweak. The band is
    # relative to this track's clean lap (see FASTLAP_MIN/MAX) so it scales per circuit.
    lo = track.base_lap_time * FASTLAP_MIN
    hi = track.base_lap_time * FASTLAP_MAX
    fl_driver, fl_time = "", float("inf")
    for rep in history:
        for s in rep.standings:
            if not s.retired and lo < s.last_lap < hi and s.last_lap < fl_time:
                fl_time, fl_driver = s.last_lap, s.name
    if not fl_driver:
        fl_time = 0.0

    # Retirements + double-DNF flashpoints, read off the incident feed.
    retirements, double_dnfs = {}, []
    for rep in history:
        for inc in rep.incidents:
            if inc.retirement and inc.driver_name not in retirements:
                retirements[inc.driver_name] = (rep.lap, inc.cause, inc.location)
            if inc.other_retired and inc.other_name not in retirements:
                retirements[inc.other_name] = (rep.lap, "collision", inc.location)
            if inc.cause == "collision" and inc.retirement and inc.other_retired:
                double_dnfs.append((inc.driver_name, inc.other_name, rep.lap, inc.location))
    retire_list = sorted(((n, lap, cause, loc) for n, (lap, cause, loc) in retirements.items()),
                         key=lambda t: t[1])

    # On-track passes for the SHARP END only. The engine resolves position every
    # lap, so the raw pass count is inflated (lots of midfield churn) and not a
    # realistic race total -- so we tally only the passes that actually mattered.
    overtakes_count = sum(1 for rep in history for ov in rep.overtakes
                          if ov.position <= 3 and ov.location != "the start")

    return RaceSummary(
        circuit=track.circuit,
        total_laps=total_laps, starters=starters, finishers=finishers,
        winner=winner.name if winner else "(no finishers)",
        team=winner.team if winner else "",
        winner_from=winner.grid_position if winner else 0,
        pole_sitter=pole.name if pole else "",
        podium=podium, drive_of_the_day=dotd, lead_changes=lead_changes,
        fastest_lap_driver=fl_driver, fastest_lap_time=fl_time,
        retirements=retire_list, double_dnfs=double_dnfs,
        overtakes_count=overtakes_count,
    )
