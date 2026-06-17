"""The roster -- a grid of history's most radical philosophers.

Pace is a base lap time in seconds (lower is faster). Consistency is lap-to-lap
variation (lower is steadier). Racecraft is wheel-to-wheel skill from 0.0 to 1.0,
and it also keeps a driver OUT of trouble -- the higher it is, the less likely a
mistake or a clumsy passing move turns into an incident.
"""

from dataclasses import dataclass


@dataclass
class Driver:
    name: str
    team: str
    pace: float          # base lap time in seconds -- lower is faster
    consistency: float   # lap-to-lap variation in seconds -- lower is steadier
    racecraft: float     # wheel-to-wheel skill, 0.0 to 1.0 -- also keeps you OUT of trouble


GRID = [
    # The Republic -- the ancient radicals
    Driver("Plato",               "Republic",     89.7, 0.15, 0.70),  # the philosopher-king: fast, composed, rules from the front
    Driver("Diogenes",            "Republic",     90.3, 0.32, 0.45),  # the Cynic: lives in a barrel, races like it -- brilliant chaos

    # Vanguard -- the revolutionaries
    Driver("Karl Marx",           "Vanguard",     90.0, 0.20, 0.55),  # inexorable: grinds the field down, lap after lap
    Driver("Rosa Luxemburg",      "Vanguard",     89.9, 0.18, 0.75),  # spontaneous, sharp, revolutionary pace

    # Black Banner -- the anarchists
    Driver("Mikhail Bakunin",     "Black Banner", 89.8, 0.26, 0.80),  # "the urge to destroy is a creative urge" -- all-out charger
    Driver("Emma Goldman",        "Black Banner", 90.1, 0.21, 0.72),  # fierce and fluent, dances through traffic

    # The Abyss -- the existentialists
    Driver("Friedrich Nietzsche", "Abyss",        89.6, 0.22, 0.62),  # will to power: quickest of all, but stares into the abyss
    Driver("Simone de Beauvoir",  "Abyss",        89.9, 0.16, 0.82),  # rigorous and precise: the complete racer

    # Ends & Means -- the strategists
    Driver("Niccolo Machiavelli", "Ends & Means", 90.2, 0.19, 0.92),  # slow car, ruthless racecraft: wins by any means necessary
    Driver("Richard Rorty",       "Ends & Means", 90.3, 0.18, 0.68),  # the ironist: adaptable, smooth, never dogmatic about a line

    # Objectivism -- a team of one
    Driver("Ayn Rand",            "Objectivism",  99.0, 0.40, 0.20),  # the individualist who won't draft, won't yield -- and won't qualify
]
