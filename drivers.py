"""The roster -- who's on the grid and what they're made of.

This file has ONE job: hold the cast of characters.
"""

from dataclasses import dataclass


@dataclass
class Driver:
    name: str
    team: str
    pace: float          # base lap time in seconds -- lower is faster
    consistency: float   # lap-to-lap variation in seconds -- lower is steadier
    racecraft: float     # wheel-to-wheel skill, 0.0 to 1.0 -- attacking AND defending


GRID = [
    Driver("Alex Mercer",  "Velocity", 89.8, 0.15, 0.70),  # fast car, strong racer
    Driver("Rohan Patel",  "Velocity", 89.9, 0.20, 0.90),  # the charger -- elite wheel-to-wheel
    Driver("Lena Brandt",  "Apex",     90.0, 0.18, 0.60),
    Driver("Diego Santos", "Apex",     90.1, 0.22, 0.25),  # quick on a clear lap, hopeless in traffic
    Driver("Yuki Tanaka",  "Meridian", 90.2, 0.17, 0.65),
    Driver("Sofia Rossi",  "Meridian", 90.3, 0.25, 0.55),
    Driver("Omar Haddad",  "Crest",    90.4, 0.20, 0.85),  # slow car, brilliant overtaker
    Driver("Ingrid Voss",  "Crest",    90.5, 0.28, 0.30),
    Driver("Caleb North",  "Pinnacle", 90.6, 0.24, 0.50),
    Driver("Mira Sokolov", "Pinnacle", 90.7, 0.30, 0.60),
]
