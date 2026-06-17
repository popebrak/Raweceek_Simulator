"""The roster -- who's on the grid and what they're made of.

This file has ONE job: hold the cast of characters. It changes only when you
add a driver or tweak someone's attributes. It knows nothing about how a race
is simulated or how results are shown.
"""

from dataclasses import dataclass


@dataclass
class Driver:
    name: str
    team: str
    pace: float          # base lap time in seconds -- lower is faster
    consistency: float   # lap-to-lap variation in seconds -- lower is steadier


GRID = [
    Driver("Alex Mercer",  "Velocity", 89.8, 0.15),
    Driver("Rohan Patel",  "Velocity", 89.9, 0.20),
    Driver("Lena Brandt",  "Apex",     90.0, 0.18),
    Driver("Diego Santos", "Apex",     90.1, 0.22),
    Driver("Yuki Tanaka",  "Meridian", 90.2, 0.17),
    Driver("Sofia Rossi",  "Meridian", 90.3, 0.25),
    Driver("Omar Haddad",  "Crest",    90.4, 0.20),
    Driver("Ingrid Voss",  "Crest",    90.5, 0.28),
    Driver("Caleb North",  "Pinnacle", 90.6, 0.24),
    Driver("Mira Sokolov", "Pinnacle", 90.7, 0.30),
]
