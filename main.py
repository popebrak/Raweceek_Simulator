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
from colour import Booth, voice, voice_show

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


def play_race(history, speed, track=None, show_telemetry=False, booth=None, end_pause=8.0):
    total_laps = len(history)
    commentary = deque(maxlen=COMMENTARY_LINES)   # the rolling buffer
    if booth is None:                              # the two voices: Vale (calls) & Benny (colour)
        booth = Booth(track)                       # shared with the pre/post-race shows when passed in

    # Which passes are worth a call depends on the circuit. Where passing is hard
    # (Monaco, Suzuka) even a midfield move is an event, so we call deeper into the
    # field; where it's cheap (Monza) we keep it to the fight for the front.
    notable_pos = NOTABLE_OVERTAKE
    if track is not None:
        notable_pos += round(track.overtaking_difficulty * 10)

    def draw(report):
        print(CLEAR_SCREEN, end="")
        print(render_standings(report.standings, report.lap, total_laps, report.conditions))
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

        # A change in the weather is a headline -- call it first, because it sets up
        # everything that follows (the spins, the dive for the pit lane). Reactive to
        # the moment, so it never reads stale.
        if report.weather_change:
            wbit = booth.for_weather(report.weather_change)
            if wbit:
                play(wbit)

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

        # The flag: on the final lap the winner's moment always gets called, AFTER
        # whatever else happened, so the race never ends on silence.
        if report.lap == total_laps:
            fin = booth.for_finish(report.standings)
            if fin:
                play(fin)

        if new_lines:
            # Tick the new calls in one at a time, spread across the lap, so the
            # feed reads live. Total time still equals one lap.
            slice_time = lap_budget / len(new_lines)
            for line in new_lines:
                commentary.append(line)
                draw(report)
                time.sleep(slice_time)
        else:
            # A quiet lap. In the closing laps the booth builds the run-in tension
            # (generated from the gap and laps left); earlier on it runs its ongoing
            # DISCUSSION, a beat at a time, so a topic unfolds across the green-flag
            # spell instead of a one-liner being fired and forgotten. Either way the
            # air is filled.
            runin = booth.for_runin(report.standings, report.lap, total_laps)
            if runin:
                for role, line in runin.turns:
                    commentary.append(voice(report.lap, role, line))
            else:
                # Some quiet laps go to the weather (temps and sky on a dry day, the
                # state of the track on a wet one) rather than the philosophy thread --
                # fresh material that exists on every single lap, which is the whole
                # reason the weather earns its place in the booth.
                ambient = (booth.weather_ambient(report.conditions)
                           if random.random() < 0.35 else None)
                if ambient:
                    for role, line in ambient.turns:
                        commentary.append(voice(report.lap, role, line))
                else:
                    for role, line in booth.next_chatter(report.standings, report.lap):
                        commentary.append(voice(report.lap, role, line))
            draw(report)
            time.sleep(lap_budget)

    # Hold the final commentary -- the run to the flag and the winner's call -- on
    # screen for a beat before the results wipe it, so it can actually be read (and,
    # until TTS lands, so there's time to follow what was just said).
    time.sleep(end_pause)

    print(CLEAR_SCREEN, end="")
    print(render_result(history[-1].standings))
    print()
    print(render_summary(summarize_race(history, track)))


def _play_show(turns, pace):
    """Play a pre/post-race show segment as paced dialogue -- each line printed in
    turn with a short beat between, so it reads like a broadcast rather than a dump.
    No lap tags (voice_show); the shows happen off the clock."""
    for role, line in turns:
        print(voice_show(role, line))
        sys.stdout.flush()
        time.sleep(pace)


def run_weekend(track=None, speed=20.0, grid_pause=10.0, show_telemetry=False,
                laps=None, difficulty=None, show_pace=1.0, end_pause=10.0):
    # Pick a circuit (by name, by object, or at random) -- the track decides the
    # race distance and how hard it is to pass.
    if track is None:
        track = random.choice(CALENDAR)
    elif isinstance(track, str):
        track = track_by_circuit(track) or random.choice(CALENDAR)

    print(track_banner(track))
    quali_results = run_qualifying(GRID, track)
    print_timing_sheet(quali_results)

    # One booth for the whole weekend -- the shows and the race share its memory, so
    # the track history set up in the preview isn't repeated mid-race.
    booth = Booth(track)

    # The pre-race show: history, the top of the grid, what to watch.
    print(DIVIDER)
    print("  COUNTDOWN TO GREEN")
    _play_show(booth.preview(quali_results, track), show_pace)

    starting_grid = [driver for driver, lap, qualified in quali_results if qualified]
    history = run_race(starting_grid, track, laps=laps, difficulty=difficulty)

    # grid_pause holds the Countdown to Green on screen so it can be read before the
    # race wipes it for the live standings board.
    print("\n  Lights out -- here we go!\n")
    time.sleep(grid_pause)
    play_race(history, speed=speed, track=track, show_telemetry=show_telemetry,
              booth=booth, end_pause=end_pause)

    # The post-race show: how it was won, where strategy turned, words from the podium.
    print()
    print(DIVIDER)
    print("  POST-RACE SHOW")
    _play_show(booth.debrief(summarize_race(history, track), history, track), show_pace)


if __name__ == "__main__":
    # Pass e.g. track="Monaco" to pick a circuit, or leave it for a random one.
    # grid_pause / end_pause hold the pre-race and post-race screens long enough to
    # read; raise them if you want even more time, drop them once TTS is reading aloud.
    run_weekend(track=None, speed=20.0, grid_pause=10.0, end_pause=10.0,
                show_telemetry=False)
