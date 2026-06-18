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
from weather import make_weather, Conditions, INTER_CROSSOVER, WET_CROSSOVER


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

# Tyre WARMUP -- the opposite end of the stint from wear. Fresh rubber off the rack
# is cold and outside its window, so the out-lap is slow; it fades over a few laps
# as temperature comes in. Magnitude scales with the COMPOUND's warmup trait (hards
# are slowest to switch on). It does NOT apply to the START tyres -- those are warmed
# on the formation lap -- only to sets fitted at a pit stop.
WARMUP_MAX = 1.4        # out-lap penalty in seconds for a neutral compound (fades to 0)
WARMUP_LAPS = 3         # how many laps the warmup penalty takes to fade away

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

# A TACTICAL undercut: a car stuck behind a rival it can't pass pulls its NEXT
# planned stop FORWARD a few laps to jump them in the pit lane. It doesn't invent a
# new stop or change compounds -- only the timing flexes -- so the plan (and the
# two-compound rule) stays intact. Whether a driver SPOTS and commits to the move is
# the strategy mind at work live: the planners pounce, the chargers sit and fume.
# (These govern the DECISION to attempt; naming a successful one after the fact is a
# separate job with its own knobs -- see UNDERCUT_WINDOW & co. in the analysis section.)
UNDERCUT_TRIGGER_GAP = 1.2    # within this many seconds of the car ahead = 'stuck behind'
UNDERCUT_BRINGFWD = 4         # how many laps early the next stop can be pulled to attack
UNDERCUT_MIN_STRATEGY = 0.45  # below this a driver never plays the undercut game
UNDERCUT_PACE_SLACK = 0.3     # don't undercut a rival more than this much quicker (they'd re-pass)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Compound:
    name: str
    grip: float          # flat per-lap time offset in seconds (negative = faster)
    wear: float          # multiplier on the wear rate (>1 wears faster)
    warmup: float        # how slow to switch on when fresh (>1 = takes longer to come in)
    family: str = "slick"   # "slick" | "inter" | "wet" -- which conditions it's for
    wet_opt: float = 0.0    # the wetness it's designed for (0 dry; see weather crossovers)


# The three dry tyres. Tuned so each is the fastest choice for SOME stint length:
# soft ~1-15 laps, medium ~16-23, hard ~24+ (before track/management scaling).
# Warmup is the OTHER half of the trade: the soft switches on almost instantly, the
# hard takes several laps to reach its window -- which is why a cold out-lap can
# sink an undercut, and why you don't fit hards for a short stint.
SOFT = Compound("soft", -0.75, 2.1, 0.6)
MEDIUM = Compound("medium", -0.05, 1.0, 1.0)
HARD = Compound("hard", 0.50, 0.5, 1.7)
COMPOUNDS = [SOFT, MEDIUM, HARD]              # the DRY planner only ever considers these

# The rain tyres. They are NOT in the dry planner's menu -- a car only reaches for
# them reactively, when the weather turns (see the reactive-tyre logic in run_race).
# `wet_opt` is where each is happiest: the intermediate around a damp track, the full
# wet around a streaming one. Run them on the wrong surface and _condition_penalty
# bites; run a slick in any wet at all and it bites savagely.
INTERMEDIATE = Compound("intermediate", 0.8, 0.9, 1.2, family="inter", wet_opt=0.40)
WET = Compound("wet", 2.2, 0.6, 1.5, family="wet", wet_opt=0.85)


# --- Weather physics ---------------------------------------------------------
# Everything here scales from ZERO when the track is dry (wetness 0), so a dry race
# behaves EXACTLY as it did before weather existed -- the tuned racing is untouched
# until it actually rains. When it does:
#   * WET_LAP_FACTOR slows EVERY car (a wet track is just slower, right tyre or not).
#   * _condition_penalty punishes the wrong tyre for the conditions -- gently for an
#     intermediate a little off its window, savagely for a slick in any standing water.
#   * mistakes multiply with wetness, and again if you're on the wrong rubber.
#   * drivers react: when the needed tyre family changes, they pit for it, and how
#     promptly is their `strategy` mind at work (the planners pounce, the chargers
#     slither around a lap too long).
WET_LAP_FACTOR = 16.0       # seconds added at full wet, even on the correct tyre
SLICK_WET_FACTOR = 70.0     # slicks on a wet track: ruinous, and quadratic in wetness
WET_MISMATCH = 22.0         # an inter/wet away from its ideal wetness, per unit off
DRY_ON_RAINS = 7.0          # a rain tyre on a bone-dry track: overheats and grains away
WET_INCIDENT = 3.0          # how much full wetness multiplies the base mistake chance
WRONGTYRE_INCIDENT = 1.8    # extra mistake multiplier when on the wrong tyre family
WEATHER_SWITCH_BASE = 0.20  # per-lap chance of reacting to a tyre-family change at all
WEATHER_SWITCH_STRAT = 0.7  # ...plus this much, scaled by the driver's strategy rating


def _needed_family(wetness):
    """Which tyre family the conditions call for -- the engine and weather.py share
    the same crossovers, so the rubber and the rain never disagree."""
    if wetness >= WET_CROSSOVER:
        return "wet"
    if wetness >= INTER_CROSSOVER:
        return "inter"
    return "slick"


def _condition_penalty(compound, wetness):
    """Per-lap time cost of the fitted tyre being wrong for the conditions. A slick
    on a wet track is a catastrophe (quadratic); a rain tyre off its window, or out
    on a drying/dry track, is merely slow."""
    if compound.family == "slick":
        return SLICK_WET_FACTOR * wetness * wetness          # 0 when dry, ruinous when wet
    pen = WET_MISMATCH * abs(wetness - compound.wet_opt)
    if wetness < 0.05:                                       # rain tyres on a dry track grain away
        pen += DRY_ON_RAINS
    return pen


def _weather_tyre(family):
    """The compound a driver bolts on for a given conditions family. Back to slicks,
    they reach for the medium -- the safe all-rounder when the track's uncertain."""
    if family == "inter":
        return INTERMEDIATE
    if family == "wet":
        return WET
    return MEDIUM


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
    last_lap: float = 0.0             # ACTUAL time for the last lap -- includes traffic, pit, incidents
    last_clean_lap: float = 0.0       # the green-flag PACE lap -- pace+damage+tyres only, no traffic/pit/incident
    aero_damage: float = 0.0          # persistent per-lap penalty: bodywork/wing
    suspension_damage: float = 0.0    # persistent per-lap penalty: mechanical
    retired: bool = False
    retired_on_lap: int = 0
    doomed_lap: int = 0               # >0 if hopeless racecraft has marked a guaranteed DNF lap
    stint_laps: int = 0               # laps on the current set of tyres -- resets at a pit stop
    pit_count: int = 0                # PLANNED stops made -- indexes the dry strategy
    stops_made: int = 0               # ALL stops (planned + undercut + weather) -- for display only
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
    clean_lap: float = 0.0       # green-flag pace lap (no traffic/pit/incident) -- for pace commentary
    interval: float = 0.0        # gap to the car directly ahead (0 for the leader) -- for battle commentary

    @property
    def damage(self):
        return self.aero_damage + self.suspension_damage

    @classmethod
    def from_car(cls, car, position, gap_to_leader, interval=0.0):
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
            clean_lap=car.last_clean_lap,
            interval=interval,
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
class Undercut:
    """A pass made in the PIT LANE, not on track. The chaser is stuck behind a
    rival, pits a lap or two earlier, and the fresh-tyre pace -- worth more than the
    pit loss -- means that when the rival finally stops, they rejoin BEHIND. The
    engine already produces these via total_time; this just NAMES the move so the
    commentary can call it. (See annotate_undercuts.)"""
    undercutter: str
    victim: str
    lap: int             # the lap the move completes -- the victim's own stop
    laps_earlier: int    # how many laps earlier the undercutter pitted
    position: int        # the place the undercutter takes (1 = the lead)


@dataclass
class LapReport:
    lap: int
    standings: list = field(default_factory=list)   # list[Standing]
    incidents: list = field(default_factory=list)   # list[Incident]
    overtakes: list = field(default_factory=list)   # list[Overtake]
    pit_stops: list = field(default_factory=list)   # list[PitStop]
    undercuts: list = field(default_factory=list)   # list[Undercut]
    conditions: Conditions = None                   # the weather this lap was run in
    weather_change: str = ""                        # set on a threshold crossing: "rain_begins" etc.


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
    """The flavour of a lone error. A spread of real driving mistakes, weighted to
    how often each tends to happen -- common little ones (running wide, a lock-up)
    far more than the rare big ones (into the wall, beached in the gravel). The cause
    sets BOTH the words the commentary uses and the kind of harm it does (see
    _make_incident): some cost mostly time, others batter the car."""
    return random.choices(
        ["off-track", "lock-up", "spin", "grass", "kerb", "wall", "gravel"],
        weights=[16, 18, 12, 12, 16, 10, 16])[0]


def _make_incident(car, lap, cause):
    """Build a SOLO incident, apply lasting damage, decide DNF.

    Each cause has its own signature. The 'soft' errors -- running wide, a lock-up,
    a spin, a trip across the grass -- mostly cost TIME right now. The 'hard' ones --
    a kerb, the wall, the gravel -- mostly inflict lasting AERO and SUSPENSION damage
    that taxes every future lap (and can let go entirely, laps later). Contact between
    cars is a separate two-car event handled by _collide.
    """
    severity = _roll_severity()
    mult = SEVERITY_MULT[severity]
    time_lost = aero = susp = 0.0

    if cause == "off-track":                            # runs out of road -- time, little damage
        time_lost = random.uniform(1.0, 3.0) * mult
        if severity != "minor":
            aero = random.uniform(0.0, 0.15) * mult
    elif cause == "lock-up":                            # flat-spots and runs deep -- mostly time
        time_lost = random.uniform(0.8, 2.2) * mult
        if severity == "major":
            aero = random.uniform(0.0, 0.10) * mult
    elif cause == "spin":                               # gathers it up / restarts -- big time cost
        time_lost = random.uniform(1.5, 3.5) * mult
        if severity != "minor":
            susp = random.uniform(0.0, 0.12) * mult
    elif cause == "grass":                              # onto the green stuff -- time, a little aero
        time_lost = random.uniform(0.8, 2.2) * mult
        if severity != "minor":
            aero = random.uniform(0.0, 0.12) * mult
    elif cause == "kerb":                               # sausage kerb -- batters the suspension
        time_lost = random.uniform(0.3, 1.0) * mult
        susp = random.uniform(0.10, 0.30) * mult
        aero = random.uniform(0.0, 0.10) * mult
    elif cause == "wall":                               # into the barrier -- heavy aero + suspension
        time_lost = random.uniform(1.5, 3.5) * mult
        aero = random.uniform(0.15, 0.35) * mult
        susp = random.uniform(0.10, 0.30) * mult
    elif cause == "gravel":                             # beached / ploughs through -- slow, and bent
        time_lost = random.uniform(2.0, 4.0) * mult
        susp = random.uniform(0.08, 0.25) * mult
        aero = random.uniform(0.05, 0.20) * mult

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
    """Running cars first (by race time), then retirements (latest DNF placed higher).
    Each running car also carries its interval to the car directly ahead."""
    active = sorted((c for c in cars if not c.retired), key=lambda c: c.total_time)
    retired = sorted((c for c in cars if c.retired), key=lambda c: -c.retired_on_lap)
    leader_time = active[0].total_time if active else 0.0
    rows = []
    prev_total = None
    for pos, c in enumerate(active + retired, start=1):
        if c.retired:
            interval = 0.0
        else:
            interval = 0.0 if prev_total is None else c.total_time - prev_total
            prev_total = c.total_time
        rows.append(Standing.from_car(c, pos, c.total_time - leader_time, interval))
    return rows


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


def _warmup_penalty(stint_lap, compound):
    """Per-lap cost of cold tyres at the START of a stint, fading over WARMUP_LAPS.
    Biggest on the out-lap (stint_lap == 1), zero once they're in their window.
    Scaled by the compound's warmup trait -- hards take longest to switch on."""
    cold = 1.0 - (stint_lap - 1) / WARMUP_LAPS          # 1.0 on the out-lap, fading to 0
    if cold <= 0.0:
        return 0.0
    return WARMUP_MAX * compound.warmup * cold


def _warmup_sum(n, compound):
    """Total warmup cost over a fresh stint of n laps -- the planner's closed form of
    _warmup_penalty summed lap by lap, so a plan is costed the way it's raced."""
    m = min(n, WARMUP_LAPS)                             # only the first WARMUP_LAPS laps are cold
    laps_cost = m - m * (m - 1) / (2 * WARMUP_LAPS)     # Sum of (1 - (s-1)/WARMUP_LAPS), s=1..m
    return WARMUP_MAX * compound.warmup * laps_cost


def _tyre_penalty(car, track):
    """The per-lap time cost of the current tyres: WEAR (grows with the stint) plus
    WARMUP (a cold-tyre penalty at the start of a stint that fades over a few laps).

    Wear is a steady linear bleed plus a quadratic 'cliff', scaled by the compound,
    the track's abrasiveness, and the driver's tyre management. Warmup is a separate,
    front-loaded cost scaled by the compound's warmup trait -- and it applies only to
    sets fitted at a pit stop, since the START tyres are warmed on the formation lap.
    """
    s = car.stint_laps
    wear = TYRE_LINEAR * s + TYRE_QUAD * s * s
    wear *= car.compound.wear                              # soft wears fast, hard slow
    wear *= track.tyre_wear                                # abrasive tracks chew tyres
    wear *= 1.0 - (car.driver.tire_management - 0.5) * TYRE_MGMT_SWING
    wear = max(0.0, wear)
    warm = _warmup_penalty(s, car.compound) if car.pit_count > 0 else 0.0
    return wear + warm


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
    # grip + wear; the constant base lap is identical across plans, so it drops out),
    # plus the WARMUP cost of starting a fresh stint on it (paid after every stop).
    cost, warm = {}, {}
    for c in COMPOUNDS:
        arr = [0.0] * (laps + 1)
        warr = [0.0] * (laps + 1)
        for n in range(1, laps + 1):
            sum_s = n * (n + 1) / 2
            sum_s2 = n * (n + 1) * (2 * n + 1) / 6
            arr[n] = c.grip * n + c.wear * w * (TYRE_LINEAR * sum_s + TYRE_QUAD * sum_s2)
            warr[n] = _warmup_sum(n, c)
        cost[c.name] = arr
        warm[c.name] = warr

    structures = []   # (best_cost, RacePlan)

    # One-stop: two distinct compounds; scan where to split the race. The opening
    # stint is warmed on the formation lap (no warmup); the post-stop stint pays it.
    for c1 in COMPOUNDS:
        for c2 in COMPOUNDS:
            if c1 is c2:
                continue
            best = None
            for a in range(1, laps):
                total = (cost[c1.name][a]
                         + cost[c2.name][laps - a] + warm[c2.name][laps - a] + PIT_LOSS)
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
                            total = (ca
                                     + cost[c2.name][b - a] + warm[c2.name][b - a]
                                     + cost[c3.name][laps - b] + warm[c3.name][laps - b]
                                     + 2 * PIT_LOSS)
                            if best is None or total < best[0]:
                                best = (total, [a, b])
                    structures.append((best[0], RacePlan([c1, c2, c3], best[1])))

    # The skill: misjudge the costs, then pick what LOOKS cheapest.
    noise = STRATEGY_NOISE * (1.0 - driver.strategy)
    chosen = min(structures, key=lambda cp: cp[0] + (random.gauss(0, noise) if noise else 0.0))
    return chosen[1]


def _wants_undercut(car, ahead, gap, lap):
    """Should this car pull its NEXT planned stop FORWARD to undercut the car ahead?

    Yes when: there's a stop left to bring forward, that stop is due within the next
    few laps (so the tyres are already near their window -- we're retiming a real
    stop, not inventing an early one), the car is stuck within undercut range of a
    rival it can't pass and isn't markedly slower than, and -- the skill -- the
    driver's strategy mind actually spots and commits to it. The chargers never do.
    """
    if car.pit_count >= len(car.plan.pit_laps):
        return False                                  # no stop left to bring forward
    next_stop = car.plan.pit_laps[car.pit_count]
    if not 0 < next_stop - lap <= UNDERCUT_BRINGFWD:
        return False                                  # only pull a stop a few laps early
    if gap > UNDERCUT_TRIGGER_GAP:
        return False                                  # not close enough to be 'stuck'
    if ahead.driver.pace < car.driver.pace - UNDERCUT_PACE_SLACK:
        return False                                  # rival clearly faster -- they'd just re-pass
    if car.driver.strategy < UNDERCUT_MIN_STRATEGY:
        return False                                  # not a strategic thinker
    return random.random() < car.driver.strategy      # the planners pounce


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

    # The weather for the whole race, decided before lights-out and then read each
    # lap. Dry unless this circuit's rain_chance rolls in.
    conditions_by_lap = make_weather(track, laps)
    prev_wetness = 0.0

    history = []

    # Resolve the standing start: this seeds each car's total_time with a real
    # grid-based spread, so the clock and track position now mean distinct things
    # and the lap loop below knows who is where from lap 1 onward.
    start_events = _run_start(cars)

    for lap in range(1, laps + 1):
        cond = conditions_by_lap[lap - 1]
        # Has the conditions crossed a tyre-crossover since last lap? That's the cue
        # for a weather CALL (and what flips everyone's needed tyre).
        weather_change = ""
        if cond.wetness >= WET_CROSSOVER > prev_wetness:
            weather_change = "rain_intensifies"
        elif cond.wetness >= INTER_CROSSOVER > prev_wetness:
            weather_change = "rain_begins"
        elif cond.wetness < INTER_CROSSOVER <= prev_wetness:
            weather_change = "track_dry"
        elif cond.wetness < WET_CROSSOVER <= prev_wetness:
            weather_change = "rain_eases"
        prev_wetness = cond.wetness

        running = sorted((c for c in cars if not c.retired), key=lambda c: c.total_time)
        # Pre-lap gap to the car directly ahead (race-time, from last lap's totals).
        # This is the 'am I stuck behind someone?' signal the undercut decision reads.
        gaps = [float("inf")] * len(running)
        for j in range(1, len(running)):
            gaps[j] = running[j].total_time - running[j - 1].total_time
        incidents = []
        overtakes = list(start_events) if lap == 1 else []
        pit_stops = []

        for i, car in enumerate(running):
            car.stint_laps += 1                                       # another lap on this set
            old_total = car.total_time
            tyre = _tyre_penalty(car, track)
            grip = car.compound.grip
            # The weather tax: a wet track is slower for everyone (WET_LAP_FACTOR), and
            # the wrong tyre for the conditions adds its own penalty on top. Both are
            # zero in the dry, so a dry lap is exactly as it always was.
            weather_pen = WET_LAP_FACTOR * cond.wetness + _condition_penalty(car.compound, cond.wetness)
            lap_time = simulate_lap(car.driver, track) + car.damage + tyre + grip + weather_pen
            car.last_clean_lap = lap_time   # the honest pace lap -- captured BEFORE traffic/pit/incident muddy it
            time_lost = 0.0
            needed = _needed_family(cond.wetness)             # which tyre the conditions call for

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

            # 2. Solo mistake: a lone error, far likelier for low-racecraft drivers --
            # and far likelier still in the wet, especially on the wrong rubber.
            wet_mult = 1.0 + WET_INCIDENT * cond.wetness
            if car.compound.family != needed:
                wet_mult *= WRONGTYRE_INCIDENT
            if random.random() < SOLO_MISTAKE_CHANCE * length_scale * (1 - car.driver.racecraft) * wet_mult:
                inc = _make_incident(car, lap, _solo_cause())
                inc.location = _pick_corner(track)
                incidents.append(inc)
                time_lost += inc.time_lost
                if inc.retirement:
                    _retire(car, lap, old_total, lap_time, time_lost)
                    continue

            # 2a. Weather stop: the conditions now call for a different tyre family than
            # the one fitted -- so the driver dives in for the right rubber. How quickly
            # they react is their strategy mind (the planners pounce; the chargers
            # slither on the wrong tyre a lap too long). This is an UNPLANNED stop: it
            # doesn't touch the dry plan's pit_count, so the slick strategy resumes
            # intact once the track comes back to them.
            if car.compound.family != needed:
                if random.random() < WEATHER_SWITCH_BASE + WEATHER_SWITCH_STRAT * car.driver.strategy:
                    old_stint = car.stint_laps
                    car.compound = _weather_tyre(needed)
                    car.stint_laps = 0
                    car.stops_made += 1
                    time_lost += PIT_LOSS
                    pit_stops.append(PitStop(car.driver.name, lap, car.stops_made,
                                             old_stint, car.compound.name))
                    car.total_time = old_total + lap_time + time_lost
                    car.last_lap = car.total_time - old_total
                    continue

            # 2b. Pit stop -- the planned lap, OR pulled forward to attack the car
            # directly ahead (a tactical undercut). Both box for the SAME planned
            # rubber and consume the same scheduled stop; the undercut just brings
            # its timing forward. The plan came from _plan_strategy; spotting the
            # undercut is the driver's `strategy` mind working live (see _wants_undercut).
            #
            # Suspended while the track needs rain tyres: nobody makes their planned
            # DRY stop in the wet. A stop whose lap fell during the rain isn't lost --
            # the `>=` lets it happen on the first dry lap after, once slicks are back.
            if needed == "slick":
                scheduled = (car.pit_count < len(car.plan.pit_laps)
                             and lap >= car.plan.pit_laps[car.pit_count])
                tactical = (not scheduled and i > 0
                            and _wants_undercut(car, running[i - 1], gaps[i], lap))
                if scheduled or tactical:
                    old_stint = car.stint_laps
                    car.pit_count += 1
                    car.stops_made += 1
                    car.compound = car.plan.compounds[car.pit_count]      # the fresh rubber
                    car.stint_laps = 0
                    time_lost += PIT_LOSS
                    pit_stops.append(PitStop(car.driver.name, lap, car.stops_made,
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

        history.append(LapReport(lap, _standings(cars), incidents, overtakes, pit_stops,
                                 conditions=cond, weather_change=weather_change))

    # Finalise the record: the live loop produced the racing; this reads the whole
    # history back and NAMES the pit-lane moves (undercuts) it created along the way.
    annotate_undercuts(history, doomed={c.driver.name for c in cars if c.doomed_lap})
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
    undercuts_count: int = 0   # passes completed in the pit lane (the undercut)


UNDERCUT_WINDOW = 6     # the rival must stop within this many laps for the move to count
UNDERCUT_CLOSE = 2.5    # how close behind (seconds) the undercutter was -- a real fight, not a fluke
UNDERCUT_STICK = 3      # the move must still hold this many laps later (or to the flag)


def annotate_undercuts(history, doomed=frozenset()):
    """Scan a finished race and attach each undercut to the lap it completes.

    An undercut: the undercutter (B) is close BEHIND a rival (A), pits a lap or two
    EARLIER, and on fresh rubber gains more than the pit stop costs -- so when A
    finally stops, A rejoins behind B. We require the order to flip exactly ACROSS
    A's stop (B behind the lap before A pits, ahead the lap A pits), which cleanly
    separates a pit move from an ordinary on-track pass. And we require it to STICK
    (B still running and ahead a few laps later), so we don't trumpet a one-lap blip
    -- or a flourish from a car that's about to retire anyway. Pure detection: the
    engine already made the move happen; we're only giving it a name.

    `doomed` names the guaranteed-DNF cars (the Objectivists): they aren't racing a
    strategy, so a pit-lane shuffle involving them is never called an undercut.
    """
    pos, tot, ret, pit_laps = {}, {}, {}, {}
    for rep in history:
        pos[rep.lap] = {s.name: s.position for s in rep.standings}
        tot[rep.lap] = {s.name: s.total_time for s in rep.standings}
        ret[rep.lap] = {s.name: s.retired for s in rep.standings}
        for ps in rep.pit_stops:
            pit_laps.setdefault(ps.driver_name, []).append(rep.lap)
    by_lap = {rep.lap: rep for rep in history}
    last_lap = history[-1].lap if history else 0
    names = list(pos[1].keys()) if 1 in pos else []

    def sticks(B, A, pA):
        check = min(pA + UNDERCUT_STICK, last_lap)
        return (not ret[check].get(B, True)        # undercutter still running...
                and pos[check][B] < pos[check][A])  # ...and still ahead

    seen = set()
    for B in names:
        for A in names:
            if A == B or A in doomed or B in doomed:
                continue
            for pB in pit_laps.get(B, []):
                for pA in pit_laps.get(A, []):
                    if not (pB < pA <= pB + UNDERCUT_WINDOW):
                        continue
                    before = pB - 1
                    if before < 1 or (B, A, pA) in seen:
                        continue
                    if not all(L in pos for L in (before, pA - 1, pA)):
                        continue
                    if B not in pos[before] or A not in pos[before]:
                        continue
                    # Close behind before B's stop, still behind the lap before A's
                    # stop, ahead the lap A stops: the swap happened in the pits.
                    if (pos[before][B] > pos[before][A]
                            and 0 < tot[before][B] - tot[before][A] < UNDERCUT_CLOSE
                            and pos[pA - 1][B] > pos[pA - 1][A]
                            and pos[pA][B] < pos[pA][A]
                            and sticks(B, A, pA)):
                        by_lap[pA].undercuts.append(
                            Undercut(B, A, pA, pA - pB, pos[pA][B]))
                        seen.add((B, A, pA))


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

    # Fastest lap, read straight off the HONEST pace lap (clean_lap). Because
    # clean_lap already excludes traffic, pit, and incident time, this no longer
    # needs the old relative band that worked around a polluted last_lap. We skip
    # lap 1 -- the standing-start scramble isn't a representative flyer.
    fl_driver, fl_time = "", float("inf")
    for rep in history:
        if rep.lap == 1:
            continue
        for s in rep.standings:
            if not s.retired and 0 < s.clean_lap < fl_time:
                fl_time, fl_driver = s.clean_lap, s.name
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
    undercuts_count = sum(len(rep.undercuts) for rep in history)

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
        undercuts_count=undercuts_count,
    )
