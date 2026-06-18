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
                     render_overtake, render_telemetry, render_result,
                     render_summary, track_banner, render_pit, render_undercut)
from colour import Booth, voice

CLEAR_SCREEN = "\033[H\033[J"
COMMENTARY_LINES = 12        # how many recent commentary lines stay on screen
NOTABLE_OVERTAKE = 3         # baseline: call passes for this position or better; hard tracks widen it
DIVIDER = "  " + "-" * 60

# What's actually worth interrupting for. A real booth doesn't call every move and
# every stop -- it calls what matters for the result. F1 scores the top ten, so a
# pass outside the points rarely makes the broadcast; a midfield pit stop never
# does. These three dials are where that judgement lives.
POINTS_POSITIONS = 10        # passes below this rarely matter -- the points are the story
PIT_CALL_POSITION = 6        # only the sharp end's stops are worth a mention
START_JUMP_WORTH = 3         # a launch this big gets called even from outside the points


def _call(text):
    """Strip the render_* '>> ' marker -- the speaker label now carries attribution,
    so the raw call no longer needs its own."""
    t = text.strip()
    return t[2:].strip() if t.startswith(">>") else t


def _overtake_worth(ov, notable_pos):
    """Is this pass worth a call? The lead and podium always are; elsewhere it has
    to be for a points place (or, off the line, a genuine flier) to make the feed."""
    if ov.location == "the start":
        return ov.position <= POINTS_POSITIONS or ov.places_gained >= START_JUMP_WORTH
    return ov.position <= min(notable_pos, POINTS_POSITIONS)


def play_race(history, speed, track=None, show_telemetry=False):
    total_laps = len(history)
    commentary = deque(maxlen=COMMENTARY_LINES)   # the rolling buffer
    booth = Booth(track)                           # the two voices: Vale (calls) & Benny (colour)

    # Which passes are worth a call depends on the circuit. Where passing is hard
    # (Monaco, Suzuka) even a midfield move is an event, so we call deeper into the
    # field; where it's cheap (Monza) we keep it to the fight for the front.
    notable_pos = NOTABLE_OVERTAKE
    if track is not None:
        notable_pos += round(track.overtaking_difficulty * 10)

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
        # Every spoken line is now stamped with a speaker (voice()): Vale makes the
        # factual call, Benny reacts -- and a Bit can be a whole exchange between them.
        pos_of = {s.name: s.position for s in report.standings}
        new_lines = []

        def say(role, text):
            new_lines.append(voice(report.lap, role, text))

        def play(bit):
            for role, line in bit.turns:            # a Bit is one or more turns of banter
                say(role, line)

        for inc in report.incidents:
            say("pbp", _call(render_commentary(inc)))
            if show_telemetry:
                tele = render_telemetry(inc).strip()
                if tele:
                    new_lines.append(f"        {tele}")
            bit = booth.for_incident(inc)           # Benny's take on the moment
            if bit:
                play(bit)
        # Call the passes worth calling -- the lead and podium always, points places
        # selectively, and a real flier off the line. Midfield churn stays silent.
        for ov in report.overtakes:
            if _overtake_worth(ov, notable_pos):
                say("pbp", _call(render_overtake(ov)))
                bit = booth.for_overtake(ov)        # the history behind the move
                if bit:
                    play(bit)
        # Pit stops: only the sharp end's are worth interrupting for -- a midfield
        # car ducking in reshuffles nothing the viewer is watching.
        for ps in report.pit_stops:
            if pos_of.get(ps.driver_name, 99) <= PIT_CALL_POSITION:
                say("pbp", _call(render_pit(ps)))
        # An undercut completes on the victim's stop lap -- always worth calling, it
        # IS the strategic story -- so it goes in right after the stop that made it.
        for uc in report.undercuts:
            say("pbp", _call(render_undercut(uc)))

        if new_lines:
            # Tick the new calls in one at a time, spread across the lap, so the
            # feed reads live. Total time still equals one lap.
            slice_time = lap_budget / len(new_lines)
            for line in new_lines:
                commentary.append(line)
                draw(report)
                time.sleep(slice_time)
        else:
            # A quiet green-flag lap -- exactly where a real booth fills the air with
            # backstory and banter. Ask the pair for a Bit; play whatever they've got.
            bit = booth.for_lull(report.standings, report.lap, total_laps)
            if bit:
                for role, line in bit.turns:
                    commentary.append(voice(report.lap, role, line))
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
    quali_results = run_qualifying(GRID, track)
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
