"""Dev-only verification harness. Mirrors the EXACT capture pipeline in
main.render_weekend_audio (preview -> play_race@1e9 -> debrief) and reports on the
script, with no audio. Run: python3 _verify.py [n_races] [--dump]"""
import sys, random
from drivers import GRID
from tracks import CALENDAR, track_by_circuit
from simulation import run_qualifying, run_race, summarize_race
from colour import Booth
from director import Director, RaceMemory
from narration import CaptureNarrator
from main import play_race


def capture_one(track):
    cap = CaptureNarrator()
    booth = Booth(track)
    director = Director(track, booth, RaceMemory())
    quali = run_qualifying(GRID, track)
    cap.script.extend(booth.preview(quali, track))
    director.open_objectivism([d.name for d in GRID if d.team == "Objectivism"])
    grid = [d for d, lap, ok in quali if ok]
    history = run_race(grid, track, laps=getattr(track, "laps", 40))
    play_race(history, speed=1e9, track=track, booth=booth, narrator=cap, director=director)
    cap.script.extend(booth.debrief(summarize_race(history, track), history, track, director.memory))
    return cap.script


def turn_text(t):
    # script turns are (role, line) tuples per the booth's show format
    if isinstance(t, (list, tuple)) and len(t) >= 2:
        return str(t[1])
    return str(t)


if __name__ == "__main__":
    n = 1
    dump = "--dump" in sys.argv
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    random.seed(7)
    exceptions = 0
    payoff_hits = 0
    payoff_markers = ("savour it now", "i've earned this one",
                      "it's never only a motor race", "made entirely by other people",
                      "waiting all race to say that", "who gets the breaks",
                      "carried his whole short life by everybody",
                      "as foretold", "start a reading group")
    for i in range(n):
        track = random.choice(CALENDAR)
        try:
            script = capture_one(track)
        except Exception as e:
            exceptions += 1
            print(f"[{i}] EXCEPTION on {getattr(track,'name','?')}: {type(e).__name__}: {e}")
            if dump:
                import traceback; traceback.print_exc()
            continue
        text = " ".join(turn_text(t).lower() for t in script)
        if any(m in text for m in payoff_markers):
            payoff_hits += 1
        if dump and i == 0:
            print(f"=== {getattr(track,'name','?')} : {len(script)} turns ===")
            for t in script:
                line = turn_text(t)
                mark = "  >> " if any(m in line.lower() for m in payoff_markers) else "     "
                print(mark, line[:170])
    print(f"\n{n} races, {exceptions} exceptions, {payoff_hits}/{n - exceptions} with Objectivism payoff")
