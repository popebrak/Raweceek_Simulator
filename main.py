"""Entry point -- runs a race weekend and plays the race back in real time.

The race plays back lap by lap. The standings board ("the flagpole") sits at the
top and refreshes each lap; below it, a COMMENTARY feed buffers -- new calls tick
in as they happen and the recent ones stay on screen, so you can follow the story
of the race as it unfolds instead of each line flashing past in a single lap.
"""

import sys
import time
import random
from collections import deque

from drivers import GRID
from tracks import CALENDAR, track_by_circuit
from simulation import run_qualifying, run_race, summarize_race
from display import (print_timing_sheet, render_standings, render_commentary,
                     render_telemetry, render_result, render_summary, track_banner)

CLEAR_SCREEN = "\033[H\033[J"
COMMENTARY_LINES = 12        # how many recent commentary lines stay on screen
DIVIDER = "  " + "-" * 60


def play_race(history, speed, track=None, show_telemetry=False):
    total_laps = len(history)
    commentary = deque(maxlen=COMMENTARY_LINES)   # the rolling buffer

    def draw(report):
        print(CLEAR_SCREEN, end="")
        print(render_standings(report.standings, report.lap, total_laps))
        print()                                   # a line of space before the commentary
        print(DIVIDER)
        print("  COMMENTARY")
        if commentary:
            for line in commentary:
                print(line)
        else:
            print("  (clean air so far...)")
        sys.stdout.flush()

    for report in history:
        lap_budget = max(report.standings[0].last_lap, 0.0) / speed

        # COMMENTARY is the spoken voice; TELEMETRY (the numbers) is an optional,
        # separate stream that never contaminates the feed a TTS engine reads.
        new_lines = []
        for inc in report.incidents:
            new_lines.append(f"  L{report.lap:>2}  {render_commentary(inc).strip()}")
            if show_telemetry:
                tele = render_telemetry(inc).strip()
                if tele:
                    new_lines.append(f"        {tele}")

        if new_lines:
            # Tick the new calls in one at a time, spread across the lap, so the
            # feed reads live. Total time still equals one lap.
            slice_time = lap_budget / len(new_lines)
            for line in new_lines:
                commentary.append(line)
                draw(report)
                time.sleep(slice_time)
        else:
            draw(report)
            time.sleep(lap_budget)

    print(CLEAR_SCREEN, end="")
    print(render_result(history[-1].standings))
    print()
    print(render_summary(summarize_race(history, track)))


def run_weekend(track=None, speed=20.0, grid_pause=5.0, show_telemetry=False,
                laps=None, difficulty=None):
    # Pick a circuit (by name, by object, or at random) -- the track decides the
    # race distance and how hard it is to pass.
    if track is None:
        track = random.choice(CALENDAR)
    elif isinstance(track, str):
        track = track_by_circuit(track) or random.choice(CALENDAR)

    print(track_banner(track))
    quali_results = run_qualifying(GRID)
    print_timing_sheet(quali_results)

    starting_grid = [driver for driver, lap, qualified in quali_results if qualified]
    history = run_race(starting_grid, track, laps=laps, difficulty=difficulty)

    # Let the qualifying sheet breathe before the race starts.
    print("\n  Lights out -- here we go!\n")
    time.sleep(grid_pause)
    play_race(history, speed=speed, track=track, show_telemetry=show_telemetry)


if __name__ == "__main__":
    # Pass e.g. track="Monaco" to pick a circuit, or leave it for a random one.
    run_weekend(track=None, speed=20.0, grid_pause=5.0, show_telemetry=False)
