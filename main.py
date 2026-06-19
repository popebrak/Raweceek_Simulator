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
from display import (print_timing_sheet, render_standings,
                     render_result, render_summary, track_banner)
from colour import Booth, voice, voice_show
from director import Director, RaceMemory
from narration import make_narrator, SilentNarrator

CLEAR_SCREEN = "\033[H\033[J"
COMMENTARY_LINES = 12        # how many recent commentary lines stay on screen
DIVIDER = "  " + "-" * 60

# What's actually worth interrupting for now lives in the director (director.py) --
# which passes, incidents, stops, and undercuts make the broadcast, and how they're
# paced, is a narrative judgement. main.py just plays back what the director hands it.


def _weather_chatter_chance(cond):
    """How often the booth bothers remarking on the weather, by how notable it is.
    Wet: it's the story, talk about it. Hot/cold dry: worth the odd mention. Fair and
    dry: a real booth barely brings it up, so this one rarely does either."""
    if cond is None:
        return 0.0
    if cond.label != "dry":
        return 0.32                       # wet/damp/greasy -- the conditions ARE the race
    if cond.track_temp >= 40 or cond.track_temp <= 16:
        return 0.07                       # a genuinely hot or cold day -- mention it now and then
    return 0.02                           # a fair, dry afternoon -- let them talk racing


def play_race(history, speed, track=None, show_telemetry=False, booth=None, end_pause=8.0,
              narrator=None, director=None):
    total_laps = len(history)
    commentary = deque(maxlen=COMMENTARY_LINES)   # the rolling buffer
    if booth is None:                              # the two voices: Phill (calls) & Benny (colour)
        booth = Booth(track)                       # shared with the pre/post-race shows when passed in
    if narrator is None:                           # no audio unless one is handed in
        narrator = SilentNarrator()
    if director is None:                           # the narrative layer: memory, arcs, pacing
        director = Director(track, booth, RaceMemory())

    def draw(report):
        if narrator.capture:        # record-only render: no terminal output at all
            return
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
        # Every spoken line is now stamped with a speaker (voice()): Phill makes the
        # factual call, Benny reacts -- and a Bit can be a whole exchange between them.
        new_lines = []        # each item is (role, text); role None = shown, never spoken

        def say(role, text):
            new_lines.append((role, text))

        def play(bit):
            for role, line in bit.turns:            # a Bit is one or more turns of banter
                say(role, line)

        # Lights out: the same green-flag call every time, the first words of the race
        # -- it lands after the preview's "stand by" and just before the getaways.
        if report is history[0]:
            say("pbp", booth.lights_out())

        # THE PRODUCER'S DESK. One call hands the whole lap to the director, which
        # gathers every event -- weather, incidents, the stewards, passes, stops and
        # undercuts -- scores them on one salience scale, always voices the mandatory
        # tier (a retirement, the lead, contact, a verdict, an undercut, a weather
        # call) and lets the rest compete for the lap's airtime budget. It hands back
        # ordered Beats, biggest story first, which play exactly like a Bit of banter.
        for beat in director.narrate(report, telemetry=show_telemetry):
            play(beat)

        # The flag: on the final lap the winner's moment always gets called, AFTER
        # whatever else happened, so the race never ends on silence.
        if report.lap == total_laps:
            fin = booth.for_finish(report.standings)
            if fin:
                play(fin)
            # The stewards' last word: cars classified away from where they crossed
            # the line, once an unserved time penalty is applied at the flag.
            for name, prov, off in report.reclassified:
                say("pbp", booth.call_reclassification(name, prov, off))

        if new_lines:
            # Tick the new calls in one at a time, spread across the lap, so the
            # feed reads live. When the narrator is silent we keep the old per-line
            # beat; when it's audible the spoken line itself is the beat, so the race
            # runs at talking speed (you can't out-pace a voice) and `speed` becomes
            # a floor rather than the clock.
            slice_time = lap_budget / len(new_lines)
            for role, text in new_lines:
                if role is None:                      # telemetry: shown, never spoken
                    commentary.append(text)
                    draw(report)
                    time.sleep(slice_time)
                    continue
                commentary.append(voice(report.lap, role, text))
                draw(report)
                if not narrator.speak(role, text):    # blocks until done when audible
                    time.sleep(slice_time)
        else:
            # A quiet lap. In the closing laps the booth builds the run-in tension
            # (generated from the gap and laps left); earlier on it runs its ongoing
            # DISCUSSION, a beat at a time, so a topic unfolds across the green-flag
            # spell instead of a one-liner being fired and forgotten. Either way the
            # air is filled.
            runin = booth.for_runin(report.standings, report.lap, total_laps)
            if runin:
                quiet_lines = list(runin.turns)
            else:
                # Periodically, the booth recaps the running order so a listener knows
                # where everyone stands -- the director decides when (see rundown()).
                rundown = director.rundown(report, total_laps)
                if rundown:
                    quiet_lines = list(rundown.turns)
                else:
                    # Weather only earns a remark when it's actually worth one. In the wet
                    # the conditions ARE the story; on a hot or cold day it's worth the odd
                    # mention; on a fair, dry afternoon a real booth would barely bring it
                    # up -- so neither does this one. The rest of the time, they talk racing.
                    ambient = (booth.weather_ambient(report.conditions)
                               if random.random() < _weather_chatter_chance(report.conditions)
                               else None)
                    if ambient:
                        quiet_lines = list(ambient.turns)
                    else:
                        quiet_lines = list(booth.next_chatter(report.standings, report.lap))

            # Same emit rule as a busy lap: show each line, speak it if we can, and
            # only fall back to a timed beat when there's no voice to pace us.
            if quiet_lines:
                slice_time = lap_budget / len(quiet_lines)
                for role, line in quiet_lines:
                    commentary.append(voice(report.lap, role, line))
                    draw(report)
                    if not narrator.speak(role, line):
                        time.sleep(slice_time)
            else:
                draw(report)
                time.sleep(lap_budget)

    # Hold the final commentary -- the run to the flag and the winner's call -- on
    # screen for a beat before the results wipe it, so it can actually be read (and,
    # when no voice is reading aloud, so there's time to follow what was just said).
    if narrator.capture:
        return                       # record-only: no screen, no results, no waiting
    time.sleep(end_pause)

    print(CLEAR_SCREEN, end="")
    print(render_result(history[-1].standings))
    print()
    print(render_summary(summarize_race(history, track)))


def _play_show(turns, pace, narrator):
    """Play a pre/post-race show segment as paced dialogue -- each line printed in
    turn with a short beat between, so it reads like a broadcast rather than a dump.
    No lap tags (voice_show); the shows happen off the clock. With a voice attached,
    the spoken line sets the pace; otherwise the printed beat does."""
    for role, line in turns:
        print(voice_show(role, line))
        sys.stdout.flush()
        if not narrator.speak(role, line):
            time.sleep(pace)


def run_weekend(track=None, speed=20.0, grid_pause=10.0, show_telemetry=False,
                laps=None, difficulty=None, show_pace=1.0, end_pause=10.0,
                narrate="silent"):
    # Pick a circuit (by name, by object, or at random) -- the track decides the
    # race distance and how hard it is to pass.
    if track is None:
        track = random.choice(CALENDAR)
    elif isinstance(track, str):
        track = track_by_circuit(track) or random.choice(CALENDAR)

    # The voice. narrate=one of "espeak" / "piper" / "kokoro" reads the booth aloud if
    # that engine is set up, and otherwise quietly falls back to the original visual-
    # only playback -- printing a one-line hint about what's missing. Use "silent" to
    # force screen-only.
    narrator = make_narrator(narrate)
    if narrator.audible:
        print("  [voices on -- the race now runs at talking speed]")
        narrator.warm_up()              # do any first-run download now, not mid-race
    elif narrator.status:
        print("  [" + narrator.status + "]")

    print(track_banner(track))
    quali_results = run_qualifying(GRID, track)
    print_timing_sheet(quali_results)

    # One booth for the whole weekend -- the shows and the race share its memory, so
    # the track history set up in the preview isn't repeated mid-race. And one director,
    # built here so its RaceMemory survives the race and feeds the post-race show -- the
    # debrief is now the PAYOFF of the arcs the director tracked.
    booth = Booth(track)
    director = Director(track, booth, RaceMemory())

    # The pre-race show: history, the top of the grid, what to watch.
    print(DIVIDER)
    print("  COUNTDOWN TO GREEN")
    _play_show(booth.preview(quali_results, track), show_pace, narrator)

    starting_grid = [driver for driver, lap, qualified in quali_results if qualified]
    history = run_race(starting_grid, track, laps=laps, difficulty=difficulty)

    # grid_pause holds the Countdown to Green on screen so a screen-only viewer can
    # read it before the race wipes it for the live standings board. The moment ANY
    # voice is in play -- live audio, or a TTS engine rendering/exporting -- the speech
    # sets the pace and this silent gap is just dead air, so we go straight to lights
    # out. (Only a truly silent, screen-only run still needs the reading beat.)
    print("\n  Lights out -- here we go!\n")
    voiced = narrator.audible or getattr(narrator, "available", False) or narrator.capture
    if not voiced:
        time.sleep(grid_pause)
    play_race(history, speed=speed, track=track, show_telemetry=show_telemetry,
              booth=booth, end_pause=end_pause, narrator=narrator, director=director)

    # The post-race show: how it was won, the fights that defined it (from the arcs the
    # director tracked), and words from the podium.
    print()
    print(DIVIDER)
    print("  POST-RACE SHOW")
    _play_show(booth.debrief(summarize_race(history, track), history, track, director.memory),
               show_pace, narrator)


def render_weekend_audio(track=None, path="race.wav", laps=None, difficulty=None,
                         gap=0.35, engine="piper"):
    """Render a whole weekend's commentary -- the Countdown to Green, the race, and
    the post-race show -- to a single WAV file. `engine` picks the voice
    ("espeak"/"piper"/"kokoro"); returns the path on success or None if that engine
    isn't set up (or no lines were produced).

    It replays the exact same line logic as a live race through a record-only narrator
    (no screen, no waiting), gathers the script, and stitches the clips together."""
    from narration import CaptureNarrator, make_narrator, render_script_to_wav
    if isinstance(track, str):
        track = track_by_circuit(track) or random.choice(CALENDAR)
    elif track is None:
        track = random.choice(CALENDAR)

    cap = CaptureNarrator()
    booth = Booth(track)
    director = Director(track, booth, RaceMemory())
    quali_results = run_qualifying(GRID, track)
    cap.script.extend(booth.preview(quali_results, track))
    starting_grid = [d for d, lap, ok in quali_results if ok]
    history = run_race(starting_grid, track, laps=laps, difficulty=difficulty)
    play_race(history, speed=1e9, track=track, booth=booth, narrator=cap, director=director)
    cap.script.extend(booth.debrief(summarize_race(history, track), history, track, director.memory))

    eng = make_narrator(engine)
    if not eng.available:
        print(f"  [cannot render audio: {eng.status or engine + ' unavailable'}]")
        return None
    eng.warm_up()                       # first-run model download up front, with feedback
    return path if render_script_to_wav(eng, cap.script, path, gap=gap) else None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run a philosophers' Grand Prix weekend in the terminal, with "
                    "optional spoken commentary.")
    parser.add_argument("--voice", choices=["silent", "espeak", "piper", "kokoro", "chatterbox"],
                        default="silent",
                        help="who reads the commentary aloud (default: silent -- text only)")
    parser.add_argument("--track", default=None,
                        help="circuit to race: venue, country, GP, or nickname "
                             "(e.g. Monza, Spa, Monaco, Silverstone, Suzuka, Interlagos). "
                             "Default: a random one.")
    parser.add_argument("--laps", type=int, default=None,
                        help="override the race distance (default: the track's own)")
    parser.add_argument("--speed", type=float, default=20.0,
                        help="playback speed multiplier; ignored once a voice paces it")
    parser.add_argument("--render", metavar="FILE", default=None,
                        help="render the whole weekend to a WAV file instead of playing "
                             "it live; needs a real --voice (espeak/piper/kokoro/chatterbox)")
    args = parser.parse_args()

    # Resolve --track up front so an unknown name is a clear error, not a silent random
    # pick. (run_weekend / render_weekend_audio accept the resolved Track object directly.)
    track = args.track
    if track is not None:
        resolved = track_by_circuit(track)
        if resolved is None:
            parser.error("unknown track %r. Available: %s"
                         % (track, ", ".join(t.circuit for t in CALENDAR)))
        track = resolved

    if args.render:
        if args.voice == "silent":
            parser.error("--render needs a real --voice: espeak, piper, or kokoro")
        out = render_weekend_audio(track=track, path=args.render,
                                   laps=args.laps, engine=args.voice)
        if out:
            print(f"  Wrote {out}")
    else:
        # grid_pause / end_pause hold the pre/post-race screens long enough to read;
        # with a voice on, the race paces itself to the speech instead.
        run_weekend(track=track, speed=args.speed, laps=args.laps,
                    grid_pause=10.0, end_pause=10.0, narrate=args.voice)
