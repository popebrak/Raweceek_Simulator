"""The engine -- turns drivers into lap times, qualifying orders, and races.

This file changes when you change *how the racing works*. It depends on the
driver data model, but it knows NOTHING about how results are displayed.
"""

import random
from dataclasses import dataclass

from drivers import Driver


# --- Tunable knobs (the "physics" of your championship) ----------------------
DIRTY_AIR_GAP = 1.0
HELD_UP_GAP = 0.7
BASE_PASS_CHANCE = 0.30
PACE_WEIGHT = 0.6
# -----------------------------------------------------------------------------


@dataclass
class CarState:
    driver: Driver
    grid_position: int = 0
    total_time: float = 0.0
    last_lap: float = 0.0


def simulate_lap(driver):
    return driver.pace + random.gauss(0, driver.consistency)


def run_qualifying(grid):
    results = [(driver, simulate_lap(driver)) for driver in grid]
    results.sort(key=lambda pair: pair[1])
    return results


def attempt_overtake(chaser, defender, difficulty):
    pace_advantage = defender.driver.pace - chaser.driver.pace
    chance = BASE_PASS_CHANCE + pace_advantage * PACE_WEIGHT - difficulty
    chance = max(0.03, min(0.95, chance))
    return random.random() < chance


def run_race(starting_grid, laps, difficulty=0.10):
    cars = [CarState(driver, grid_position=i + 1)
            for i, driver in enumerate(starting_grid)]

    for lap in range(1, laps + 1):
        cars.sort(key=lambda c: c.total_time)
        for i, car in enumerate(cars):
            car.last_lap = simulate_lap(car.driver)
            natural_time = car.total_time + car.last_lap

            if i == 0:
                car.total_time = natural_time
                continue

            ahead = cars[i - 1]
            if natural_time < ahead.total_time + DIRTY_AIR_GAP:
                if attempt_overtake(car, ahead, difficulty):
                    car.total_time = natural_time
                else:
                    car.total_time = ahead.total_time + HELD_UP_GAP
            else:
                car.total_time = natural_time

    cars.sort(key=lambda c: c.total_time)
    return cars
