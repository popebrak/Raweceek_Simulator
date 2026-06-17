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
"""

import random
from dataclasses import dataclass, field

from drivers import Driver


# --- Pace / overtaking knobs -------------------------------------------------
DIRTY_AIR_GAP = 1.0
HELD_UP_GAP = 0.7
BASE_PASS_CHANCE = 0.30
PACE_WEIGHT = 0.6
RACECRAFT_WEIGHT = 0.25

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

# Collisions take two. A big (major) hit can pitch either car out -- and rolling
# it for each independently means a really big one sometimes takes BOTH. The car
# defending takes a smaller share of a glancing blow, but a major shunt wrecks both.
COLLISION_DNF_CHANCE = 0.42     # per-car DNF chance in a MAJOR collision
DEFENDER_SHARE = {"minor": 0.4, "moderate": 0.6, "major": 1.0}  # damage the passed car absorbs
# -----------------------------------------------------------------------------


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

    @property
    def damage(self):
        return self.aero_damage + self.suspension_damage


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


@dataclass
class LapReport:
    lap: int
    standings: list = field(default_factory=list)   # list[Standing]
    incidents: list = field(default_factory=list)   # list[Incident]


def simulate_lap(driver):
    return driver.pace + random.gauss(0, driver.consistency)


def run_qualifying(grid):
    """Each driver sets one flying lap. Apply the 107% rule.

    Returns a list of (driver, lap, qualified) sorted fastest first. A driver is
    'qualified' only if their lap is within 107% of pole.
    """
    results = [(driver, simulate_lap(driver)) for driver in grid]
    results.sort(key=lambda pair: pair[1])
    cutoff = results[0][1] * QUALIFYING_CUTOFF
    return [(driver, lap, lap <= cutoff) for driver, lap in results]


def attempt_overtake(chaser, defender, difficulty):
    pace_advantage = defender.driver.pace - chaser.driver.pace
    skill_advantage = chaser.driver.racecraft - defender.driver.racecraft
    chance = (BASE_PASS_CHANCE
              + pace_advantage * PACE_WEIGHT
              + skill_advantage * RACECRAFT_WEIGHT
              - difficulty)
    chance = max(0.03, min(0.95, chance))
    return random.random() < chance


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
    return [
        Standing(pos, c.driver.name, c.driver.team, c.grid_position,
                 c.total_time, c.last_lap, c.total_time - leader_time,
                 c.aero_damage, c.suspension_damage, c.retired, c.retired_on_lap)
        for pos, c in enumerate(ordered, start=1)
    ]


def _retire(car, lap, old_total, lap_time, time_lost):
    car.retired, car.retired_on_lap = True, lap
    car.total_time = old_total + lap_time + time_lost
    car.last_lap = car.total_time - old_total


def run_race(starting_grid, laps, difficulty=0.10):
    cars = [CarState(driver, grid_position=i + 1)
            for i, driver in enumerate(starting_grid)]

    # Hopeless racecraft is a sentence, not a tendency: pick the lap on which the
    # inevitable race-ending mistake arrives. (They still flail their way there.)
    for car in cars:
        if car.driver.racecraft <= RACECRAFT_FLOOR:
            car.doomed_lap = random.randint(1, laps)

    history = []

    for lap in range(1, laps + 1):
        running = sorted((c for c in cars if not c.retired), key=lambda c: c.total_time)
        incidents = []

        for i, car in enumerate(running):
            old_total = car.total_time
            lap_time = simulate_lap(car.driver) + car.damage   # both damages tax the lap
            time_lost = 0.0

            # 0. Hopeless racecraft: the inevitable, race-ending error finally arrives
            if car.doomed_lap and lap >= car.doomed_lap:
                car.retired, car.retired_on_lap = True, lap
                incidents.append(Incident(car.driver.name, lap, "over the limit",
                                          "major", 0.0, 0.0, 0.0, True))
                continue

            # 1. Delayed failure: carried damage can finally let go, laps later
            if car.damage > 0 and random.random() < DAMAGE_FAILURE_FACTOR * car.damage:
                car.retired, car.retired_on_lap = True, lap
                incidents.append(Incident(car.driver.name, lap, "damage failure",
                                          "major", 0.0, 0.0, 0.0, True))
                continue

            # 2. Solo mistake: a lone error, far likelier for low-racecraft drivers
            if random.random() < SOLO_MISTAKE_CHANCE * (1 - car.driver.racecraft):
                inc = _make_incident(car, lap, _solo_cause())
                incidents.append(inc)
                time_lost += inc.time_lost
                if inc.retirement:
                    _retire(car, lap, old_total, lap_time, time_lost)
                    continue

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
                car.total_time = provisional                      # move stuck -- through cleanly
            else:
                # The move didn't come off -- risk of contact, worse if clumsy
                if random.random() < CONTACT_CHANCE * (1 - car.driver.racecraft):
                    inc, lost, chaser_out = _collide(car, ahead, lap)
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

        history.append(LapReport(lap, _standings(cars), incidents))

    return history


# --- Post-race analysis ------------------------------------------------------
# This reads the finished `history` and distils the story out of it. It is
# ANALYSIS, not presentation: it returns facts (names, laps, causes), and the
# display layer decides the words. The same "scan the frames, pull out events"
# move is what the live commentary engine will be built on.

@dataclass
class RaceSummary:
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
    retirements: list          # [(name, lap, cause)] -- raw cause, words live in display
    double_dnfs: list          # [(chaser, defender, lap)] from major collisions


def summarize_race(history):
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
    # separately in run_race -- a good, well-contained future tweak.
    fl_driver, fl_time = "", float("inf")
    for rep in history:
        for s in rep.standings:
            if not s.retired and 80.0 < s.last_lap < 100.0 and s.last_lap < fl_time:
                fl_time, fl_driver = s.last_lap, s.name
    if not fl_driver:
        fl_time = 0.0

    # Retirements + double-DNF flashpoints, read off the incident feed.
    retirements, double_dnfs = {}, []
    for rep in history:
        for inc in rep.incidents:
            if inc.retirement and inc.driver_name not in retirements:
                retirements[inc.driver_name] = (rep.lap, inc.cause)
            if inc.other_retired and inc.other_name not in retirements:
                retirements[inc.other_name] = (rep.lap, "collision")
            if inc.cause == "collision" and inc.retirement and inc.other_retired:
                double_dnfs.append((inc.driver_name, inc.other_name, rep.lap))
    retire_list = sorted(((n, lap, cause) for n, (lap, cause) in retirements.items()),
                         key=lambda t: t[1])

    return RaceSummary(
        total_laps=total_laps, starters=starters, finishers=finishers,
        winner=winner.name if winner else "(no finishers)",
        team=winner.team if winner else "",
        winner_from=winner.grid_position if winner else 0,
        pole_sitter=pole.name if pole else "",
        podium=podium, drive_of_the_day=dotd, lead_changes=lead_changes,
        fastest_lap_driver=fl_driver, fastest_lap_time=fl_time,
        retirements=retire_list, double_dnfs=double_dnfs,
    )
