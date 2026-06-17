"""Entry point -- runs a race weekend and plays the race back in real time."""

import time

from drivers import GRID
from simulation import run_qualifying, run_race
from display import (print_timing_sheet, render_standings,
                     render_incident, render_result)

CLEAR_SCREEN = "\033[H\033[J"


def play_race(history, speed):
    total_laps = len(history)
    for report in history:
        print(CLEAR_SCREEN, end="")
        print(render_standings(report.standings, report.lap, total_laps))
        for incident in report.incidents:
            print(render_incident(incident))
        leader_lap_time = report.standings[0].last_lap
        time.sleep(max(leader_lap_time, 0.0) / speed)

    print(CLEAR_SCREEN, end="")
    print(render_result(history[-1].standings))


def run_weekend(difficulty=0.10, speed=20.0):
    quali_results = run_qualifying(GRID)
    print_timing_sheet(quali_results)

    starting_grid = [driver for driver, lap, qualified in quali_results if qualified]
    history = run_race(starting_grid, laps=20, difficulty=difficulty)

    print("\n  Lights out -- here we go!\n")
    time.sleep(40.0 / speed)
    play_race(history, speed=speed)


if __name__ == "__main__":
    run_weekend(difficulty=0.10, speed=20.0)
