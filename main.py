"""Entry point -- runs a race weekend.

This is the ONLY file you run directly. Its job is to wire the other three
together: get the drivers, run the sessions, show the results.
"""

from drivers import GRID
from simulation import run_qualifying, run_race
from display import print_timing_sheet, print_race_result


def run_weekend(difficulty=0.10):
    quali_results = run_qualifying(GRID)
    print_timing_sheet(quali_results)

    starting_grid = [driver for driver, lap in quali_results]

    race_result = run_race(starting_grid, laps=20, difficulty=difficulty)
    print_race_result(race_result)


if __name__ == "__main__":
    run_weekend(difficulty=0.10)
