"""The roster -- a full 20-car grid of history's most radical philosophers.

Pace is a base lap time in seconds (lower is faster). Consistency is lap-to-lap
variation (lower is steadier). Racecraft is wheel-to-wheel skill from 0.0 to 1.0,
and it also keeps a driver OUT of trouble -- the higher it is, the less likely a
mistake or a clumsy passing move turns into an incident. Racecraft at or below
RACECRAFT_FLOOR (see simulation.py) is hopeless: a guaranteed race-ending error.

Launch is the getaway off the line, 0.0 to 1.0 (0.5 is an average start). It is a
DISTINCT axis from racecraft on purpose -- a brilliant wheel-to-wheel racer can
still bog down at the lights, and a chaotic backmarker can rocket away. It feeds
the standing start in simulation._run_start.

Tyre management is how gently a driver uses the rubber, 0.0 to 1.0 (0.5 neutral).
A high value means tyres wear more slowly -- longer stints, later stops, the
undercut at their mercy. Also decorrelated on purpose: some of the quickest, most
aggressive drivers are the hardest on their tyres. It feeds simulation._tyre_penalty.
We do NOT model graining or core temperature as physics; this one number IS our
abstraction for the whole craft of keeping a tyre alive. See ROADMAP.md.

(Strategy is still to come -- it needs the pit/team machinery first. See ROADMAP.md.)
"""

from dataclasses import dataclass


@dataclass
class Driver:
    name: str
    team: str
    pace: float              # base lap time in seconds -- lower is faster
    consistency: float       # lap-to-lap variation in seconds -- lower is steadier
    racecraft: float         # wheel-to-wheel skill, 0.0 to 1.0 -- also keeps you OUT of trouble
    launch: float = 0.5      # getaway off the line, 0.0 to 1.0 -- a separate gift from racecraft
    tire_management: float = 0.5  # how gently the tyres are used, 0.0 to 1.0 -- higher wears slower


GRID = [
    # Republic -- the ancients who'd burn the cave down
    Driver("Plato",                "Republic",      89.7, 0.15, 0.70, 0.55, 0.78),  # composed, rules from the front -- and looks after his rubber
    Driver("Diogenes",             "Republic",      90.3, 0.32, 0.45, 0.72, 0.32),  # the Cynic: explosive but feral -- destroys a set of tyres

    # Vanguard -- the revolutionaries
    Driver("Karl Marx",            "Vanguard",      90.0, 0.20, 0.55, 0.40, 0.82),  # inexorable: slow away, but nurses the tyres and grinds you down on a long stint
    Driver("Rosa Luxemburg",       "Vanguard",      89.9, 0.18, 0.75, 0.74, 0.60),  # spontaneous, sharp -- spends the tyre to make the move

    # Black Banner -- the anarchists
    Driver("Mikhail Bakunin",      "Black Banner",  89.8, 0.26, 0.80, 0.82, 0.30),  # all-out charger: blistering pace and launch, but eats his tyres alive
    Driver("Emma Goldman",         "Black Banner",  90.1, 0.21, 0.72, 0.75, 0.50),  # fierce and fluent: a flying start, average on her tyres

    # Abyss -- the existentialists
    Driver("Friedrich Nietzsche",  "Abyss",         89.6, 0.22, 0.62, 0.70, 0.35),  # will to power: the quickest, and the hardest on his tyres -- a gamble every stint
    Driver("Simone de Beauvoir",   "Abyss",         89.9, 0.16, 0.82, 0.66, 0.82),  # rigorous and precise: a complete racer who makes a set last

    # Ends & Means -- the strategists
    Driver("Niccolò Machiavelli",  "Ends & Means",  90.2, 0.19, 0.92, 0.55, 0.88),  # the strategist: ruthless racecraft and a tyre-whisperer -- built for the long game
    Driver("Richard Rorty",        "Ends & Means",  90.3, 0.18, 0.68, 0.62, 0.74),  # the ironist: smooth and adaptable, easy on the rubber

    # Frankfurt -- the critical theorists
    Driver("Theodor Adorno",       "Frankfurt",     90.4, 0.20, 0.66, 0.42, 0.58),  # the pessimist: slow away, fair on his tyres, expects the worst
    Driver("Herbert Marcuse",      "Frankfurt",     90.2, 0.23, 0.70, 0.70, 0.45),  # the Great Refusal: attacks relentlessly -- and pays for it in tyre wear

    # Différance -- the post-structuralists
    Driver("Michel Foucault",      "Différance",    90.0, 0.22, 0.74, 0.71, 0.68),  # patient, probing: looks after the tyre, strikes when the gap opens
    Driver("Jacques Derrida",      "Différance",    90.5, 0.24, 0.71, 0.50, 0.55),  # impossible to pin down: erratic everywhere, tyres included

    # Liberation -- the anti-colonial radicals
    Driver("Frantz Fanon",         "Liberation",    90.1, 0.21, 0.78, 0.78, 0.48),  # fierce and decisive -- lightning starts, but fights the tyre as hard as the rival
    Driver("Aimé Césaire",         "Liberation",    90.4, 0.19, 0.69, 0.58, 0.66),  # lyrical precision: measured, kind to the rubber

    # Rights of Man -- the revolutionary pamphleteers
    Driver("Thomas Paine",         "Rights of Man", 90.3, 0.22, 0.67, 0.64, 0.62),  # bold, plain-spoken: steady and unfussy on his tyres
    Driver("Mary Wollstonecraft",  "Rights of Man", 90.2, 0.18, 0.76, 0.66, 0.76),  # rigorous and principled: quick, clean, and gentle on a set

    # Objectivism -- two individualists who will not yield, draft, or finish.
    # Racecraft 0.0: their philosophy IS their undoing. They retire every race.
    Driver("Ayn Rand",             "Objectivism",   90.6, 0.30, 0.00, 0.25, 0.20),  # refuses every compromise, including the one that saves a tyre
    Driver("Max Stirner",          "Objectivism",   90.7, 0.32, 0.00, 0.22, 0.20),  # the egoist: the tyre, like everything else, is beneath his concern
]
