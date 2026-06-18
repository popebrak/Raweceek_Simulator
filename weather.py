"""Weather -- the conditions a race is run in, generated per weekend.

A race's weather is a list of per-lap Conditions, built once before lights-out from
the track's own tendencies (some circuits are wetter, hotter, colder than others)
and then read by the engine every lap. The master dial is WETNESS, 0.0 (bone dry)
to 1.0 (full wet); air and track temperature ride alongside it.

Most races stay dry -- which still gives the booth temperatures and skies to talk
about, fresh every lap because they drift -- but sometimes a shower arrives, and
then the whole race turns over: slicks give way to intermediates and then to full
wets, lap times balloon, mistakes multiply, and the strategists who read the sky
earliest win the day. The simulation reads these numbers; it doesn't live here.

The crossovers below are where one tyre family gives way to the next, and the
engine uses the very same thresholds to decide which tyre a driver NEEDS -- so the
weather and the rubber stay in lockstep.
"""

import random
from dataclasses import dataclass


INTER_CROSSOVER = 0.25   # at/above this wetness, slicks give way to intermediates
WET_CROSSOVER = 0.60     # at/above this, intermediates give way to full wets


@dataclass(frozen=True)
class Conditions:
    wetness: float       # 0.0 bone dry .. 1.0 full wet
    air_temp: float      # degrees C
    track_temp: float    # degrees C -- warmer than air in dry sun, drops in the rain

    @property
    def label(self):
        if self.wetness >= WET_CROSSOVER:
            return "wet"
        if self.wetness >= INTER_CROSSOVER:
            return "damp"
        if self.wetness > 0.03:
            return "greasy"
        return "dry"


def make_weather(track, laps, rng=random):
    """Build a per-lap weather script for one race. Returns list[Conditions], one
    per lap. Dry unless this track's rain_chance rolls in -- and even then it's a
    passing system (build, hold, ease), not a switch flicked on for the whole race."""
    lo, hi = getattr(track, "temp_range", (16, 30))
    air0 = rng.uniform(lo, hi)
    sun = rng.uniform(6.0, 16.0)                   # how much hotter the dry track runs than the air

    wet = [0.0] * laps
    if rng.random() < getattr(track, "rain_chance", 0.18):
        peak = rng.uniform(0.40, 0.95)             # how hard it ends up raining
        start = rng.randint(1, max(1, laps - 5))
        ramp = rng.randint(2, 5)                    # laps for it to build
        hold = rng.randint(2, max(2, laps // 6))   # laps at full intensity
        ease = rng.randint(3, 7)                    # laps to dry back out
        for k in range(ramp + hold + ease):
            lap_i = start - 1 + k
            if lap_i >= laps:
                break
            if k < ramp:
                w = peak * (k + 1) / ramp
            elif k < ramp + hold:
                w = peak
            else:
                w = peak * (1 - (k - ramp - hold + 1) / (ease + 1))
            wet[lap_i] = max(0.0, min(1.0, w))

    out = []
    for i in range(laps):
        w = wet[i]
        air = air0 + rng.uniform(-1.0, 1.0)        # gentle drift lap to lap
        # The track runs hotter than the air in the dry sun, and cools sharply as it
        # gets wet -- so track_temp falls away exactly when the rain matters most.
        ttemp = air + sun * (1.0 - w) - 8.0 * w + rng.uniform(-1.0, 1.0)
        out.append(Conditions(round(w, 3), round(air, 1), round(ttemp, 1)))
    return out
