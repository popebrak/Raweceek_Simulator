"""The engine -- lap times, qualifying (with the 107% rule), races, incidents,
damage, and DNFs.

Damage is not one faceless number. An incident has a CAUSE (contact, the wall, a
sausage kerb, an off-track moment) and a SEVERITY (minor/moderate/major), and it
does specific harm to specific systems -- AERO and SUSPENSION -- each of which
taxes every remaining lap. Carried damage also quietly raises the chance of a
later failure, so a small early knock can end a race many laps on. Major hits can
retire a car outright (DNF).

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
# Tuned to modern-F1 attrition: ~0.8 retirements per race over this 10-car, 20-lap
# run (≈1.7 per equivalent 20-car grid), with ~40% of races finishing clean.
SOLO_MISTAKE_CHANCE = 0.030     # lone error per lap, before skill-scaling
CONTACT_CHANCE = 0.14           # extra risk when a passing move fails
MAJOR_DNF_CHANCE = 0.60         # chance a 'major' incident ends the race on the spot
DAMAGE_FAILURE_FACTOR = 0.016   # per-lap DNF risk per 1.0s/lap of carried damage
SEVERITY_SPLIT = (0.58, 0.23)   # P(minor), P(moderate); remainder is major
SEVERITY_MULT = {"minor": 1.0, "moderate": 2.2, "major": 4.5}
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
    cause: str           # "contact" | "wall" | "kerb" | "off-track" | "damage failure"
    severity: str        # "minor" | "moderate" | "major"
    time_lost: float
    aero_added: float
    suspension_added: float
    retirement: bool


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
    """Build an incident of the given cause, apply lasting damage, decide DNF.

    An off-track mostly costs time now; kerbs and contact mostly cost lasting
    damage (suspension and aero) that taxes every future lap.
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
    elif cause == "contact":
        time_lost = random.uniform(0.5, 2.0) * mult
        aero = random.uniform(0.10, 0.30) * mult         # wings are fragile
        susp = random.uniform(0.05, 0.20) * mult

    car.aero_damage += aero
    car.suspension_damage += susp

    retirement = (severity == "major" and random.random() < MAJOR_DNF_CHANCE)
    return Incident(car.driver.name, lap, cause, severity,
                    time_lost, aero, susp, retirement)


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
            if provisional < ahead.total_time + DIRTY_AIR_GAP:
                if attempt_overtake(car, ahead, difficulty):
                    car.total_time = provisional
                else:
                    # The move didn't come off -- risk of contact, worse if clumsy
                    if random.random() < CONTACT_CHANCE * (1 - car.driver.racecraft):
                        inc = _make_incident(car, lap, "contact")
                        incidents.append(inc)
                        time_lost += inc.time_lost
                        if inc.retirement:
                            _retire(car, lap, old_total, lap_time, time_lost)
                            continue
                    car.total_time = ahead.total_time + HELD_UP_GAP + time_lost
            else:
                car.total_time = provisional

            car.last_lap = car.total_time - old_total

        history.append(LapReport(lap, _standings(cars), incidents))

    return history
