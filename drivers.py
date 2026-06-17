"""The roster -- a full 20-car grid of history's most radical philosophers.

Pace is a base lap time in seconds (lower is faster). Consistency is lap-to-lap
variation (lower is steadier). Racecraft is wheel-to-wheel skill from 0.0 to 1.0,
and it also keeps a driver OUT of trouble -- the higher it is, the less likely a
mistake or a clumsy passing move turns into an incident. Racecraft at or below
RACECRAFT_FLOOR (see simulation.py) is hopeless: a guaranteed race-ending error.
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
    # Republic -- the ancients who'd burn the cave down
    Driver("Plato",                "Republic",      89.7, 0.15, 0.70),  # the philosopher-king: fast, composed, rules from the front
    Driver("Diogenes",             "Republic",      90.3, 0.32, 0.45),  # the Cynic: lives in a barrel, races like it -- brilliant chaos

    # Vanguard -- the revolutionaries
    Driver("Karl Marx",            "Vanguard",      90.0, 0.20, 0.55),  # inexorable: grinds the field down, lap after lap
    Driver("Rosa Luxemburg",       "Vanguard",      89.9, 0.18, 0.75),  # spontaneous, sharp, revolutionary pace

    # Black Banner -- the anarchists
    Driver("Mikhail Bakunin",      "Black Banner",  89.8, 0.26, 0.80),  # "the urge to destroy is a creative urge" -- all-out charger
    Driver("Emma Goldman",         "Black Banner",  90.1, 0.21, 0.72),  # fierce and fluent, dances through traffic

    # Abyss -- the existentialists
    Driver("Friedrich Nietzsche",  "Abyss",         89.6, 0.22, 0.62),  # will to power: quickest of all, but stares into the abyss
    Driver("Simone de Beauvoir",   "Abyss",         89.9, 0.16, 0.82),  # rigorous and precise: the complete racer

    # Ends & Means -- the strategists
    Driver("Niccolò Machiavelli",  "Ends & Means",  90.2, 0.19, 0.92),  # slow car, ruthless racecraft: wins by any means necessary
    Driver("Richard Rorty",        "Ends & Means",  90.3, 0.18, 0.68),  # the ironist: adaptable, smooth, never dogmatic about a line

    # Frankfurt -- the critical theorists
    Driver("Theodor Adorno",       "Frankfurt",     90.4, 0.20, 0.66),  # the pessimist: brilliant, gloomy, distrusts the whole spectacle
    Driver("Herbert Marcuse",      "Frankfurt",     90.2, 0.23, 0.70),  # the Great Refusal: New Left firebrand, attacks relentlessly

    # Différance -- the post-structuralists
    Driver("Michel Foucault",      "Différance",    90.0, 0.22, 0.74),  # probes every boundary, finds the gap nobody defends
    Driver("Jacques Derrida",      "Différance",    90.5, 0.24, 0.71),  # deconstructs the racing line itself -- impossible to pin down

    # Liberation -- the anti-colonial radicals
    Driver("Frantz Fanon",         "Liberation",    90.1, 0.21, 0.78),  # fierce and decisive, fights for every inch
    Driver("Aimé Césaire",         "Liberation",    90.4, 0.19, 0.69),  # lyrical precision, métier of the perfect line

    # Rights of Man -- the revolutionary pamphleteers
    Driver("Thomas Paine",         "Rights of Man", 90.3, 0.22, 0.67),  # bold, plain-spoken, common-sense racer
    Driver("Mary Wollstonecraft",  "Rights of Man", 90.2, 0.18, 0.76),  # rigorous and principled, quick and clean

    # Objectivism -- two individualists who will not yield, draft, or finish.
    # Racecraft 0.0: their philosophy IS their undoing. They retire every race.
    Driver("Ayn Rand",             "Objectivism",   90.6, 0.30, 0.00),  # won't draft, won't yield, won't cooperate -- terminal
    Driver("Max Stirner",          "Objectivism",   90.7, 0.32, 0.00),  # the egoist: nothing is higher than the self, least of all the car ahead
]
