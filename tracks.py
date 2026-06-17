"""The circuits -- a calendar of iconic tracks, as DATA the engine reasons about.

A track is not decoration. Each one carries numbers the simulation actually uses:

  * lap_length_km + race_distance_km  ->  how many LAPS the race runs (the real
    F1 rule: the fewest laps exceeding ~305 km; Monaco is the historic short one).
  * base_lap_time                     ->  the representative clean lap in seconds.
    Driver pace is an abstract ~90s skill figure; the engine scales it to this so
    Monaco laps read ~1:13 and Spa ~1:45 instead of an abstract ~1:30 everywhere.
  * overtaking_difficulty             ->  fed straight into the engine's pass
    maths. Monza is a slipstreaming free-for-all; Monaco is a fortress.
  * corners (some flagged `overtaking`) ->  WHERE an incident or a pass happens,
    so commentary can say "down the inside at the Nouvelle Chicane". Passing moves
    gravitate to the overtaking corners.

Like drivers.py, this file is pure data -- no logic. The engine (simulation.py)
reads these numbers; it doesn't live here.
"""

import math
from dataclasses import dataclass


@dataclass
class Corner:
    name: str
    overtaking: bool = False     # is this a realistic place to make a move?


@dataclass
class Track:
    name: str                    # the Grand Prix, e.g. "Italian Grand Prix"
    circuit: str                 # the venue, e.g. "Monza"
    country: str
    lap_length_km: float
    base_lap_time: float         # representative clean lap, in seconds
    overtaking_difficulty: float # higher = harder to pass (feeds attempt_overtake)
    character: str               # one-line flavour for the pre-race banner
    corners: list                # list[Corner]
    race_distance_km: float = 305.0   # F1 standard; Monaco is the exception

    @property
    def laps(self):
        """Real F1 rule: the fewest laps whose distance exceeds the target."""
        return math.ceil(self.race_distance_km / self.lap_length_km)


CALENDAR = [
    Track(
        "Italian Grand Prix", "Monza", "Italy",
        lap_length_km=5.793, base_lap_time=81.0, overtaking_difficulty=0.03,
        character="The Temple of Speed -- long straights, big tows, easy passing.",
        corners=[
            Corner("the Variante del Rettifilo", overtaking=True),
            Corner("Curva Grande"),
            Corner("the Variante della Roggia", overtaking=True),
            Corner("Lesmo 1"),
            Corner("Lesmo 2"),
            Corner("the Variante Ascari"),
            Corner("the Parabolica"),
        ],
    ),
    Track(
        "Belgian Grand Prix", "Spa-Francorchamps", "Belgium",
        lap_length_km=7.004, base_lap_time=105.0, overtaking_difficulty=0.07,
        character="Long, fast and sweeping -- the Kemmel straight rewards a brave tow.",
        corners=[
            Corner("La Source", overtaking=True),
            Corner("Eau Rouge"),
            Corner("Raidillon"),
            Corner("Les Combes", overtaking=True),
            Corner("Pouhon"),
            Corner("Stavelot"),
            Corner("the Bus Stop chicane", overtaking=True),
        ],
    ),
    Track(
        "Monaco Grand Prix", "Monte Carlo", "Monaco",
        lap_length_km=3.337, base_lap_time=73.0, overtaking_difficulty=0.45,
        race_distance_km=260.0,
        character="The jewel in the crown -- and a fortress. Track position is everything.",
        corners=[
            Corner("Sainte Devote"),
            Corner("Massenet"),
            Corner("Casino Square"),
            Corner("Mirabeau"),
            Corner("the Grand Hotel Hairpin"),
            Corner("the Tunnel"),
            Corner("the Nouvelle Chicane", overtaking=True),
            Corner("Tabac"),
            Corner("the Swimming Pool"),
            Corner("Rascasse"),
        ],
    ),
    Track(
        "British Grand Prix", "Silverstone", "United Kingdom",
        lap_length_km=5.891, base_lap_time=88.0, overtaking_difficulty=0.12,
        character="Fast and flowing -- Maggotts and Becketts, then a run to Stowe.",
        corners=[
            Corner("Abbey"),
            Corner("the Wellington Straight"),
            Corner("Brooklands"),
            Corner("Luffield"),
            Corner("Copse"),
            Corner("Maggotts"),
            Corner("Becketts"),
            Corner("Stowe", overtaking=True),
            Corner("Vale", overtaking=True),
            Corner("Club"),
        ],
    ),
    Track(
        "Japanese Grand Prix", "Suzuka", "Japan",
        lap_length_km=5.807, base_lap_time=91.0, overtaking_difficulty=0.22,
        character="A flowing figure-of-eight -- technical, narrow, hard to pass.",
        corners=[
            Corner("the First Curve"),
            Corner("the S Curves"),
            Corner("Dunlop"),
            Corner("Degner"),
            Corner("the Hairpin", overtaking=True),
            Corner("Spoon Curve"),
            Corner("130R"),
            Corner("the Casio Triangle chicane", overtaking=True),
        ],
    ),
    Track(
        "Sao Paulo Grand Prix", "Interlagos", "Brazil",
        lap_length_km=4.309, base_lap_time=71.0, overtaking_difficulty=0.10,
        character="Short, anticlockwise and full of elevation -- the Senna S bites.",
        corners=[
            Corner("the Senna S", overtaking=True),
            Corner("Curva do Sol"),
            Corner("the Reta Oposta"),
            Corner("Descida do Lago", overtaking=True),
            Corner("Ferradura"),
            Corner("Pinheirinho"),
            Corner("Bico de Pato"),
            Corner("Mergulho"),
            Corner("Juncao"),
            Corner("the Arquibancadas"),
        ],
    ),
]


def track_by_circuit(name):
    """Look up a track by its venue name (case-insensitive). None if not found."""
    for t in CALENDAR:
        if t.circuit.lower() == name.lower():
            return t
    return None
