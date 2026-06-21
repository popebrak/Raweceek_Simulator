"""The roster -- a full 20-car grid of history's most radical philosophers.

Pace is a base lap time in seconds (lower is faster). Consistency is lap-to-lap
variation (lower is steadier). Racecraft is wheel-to-wheel skill from 0.0 to 1.0,
and it also keeps a driver OUT of trouble -- the higher it is, the less likely a
mistake or a clumsy passing move turns into an incident. Racecraft at or below
RACECRAFT_FLOOR (see simulation.py) is hopeless: a guaranteed race-ending error.

Launch is the getaway off the line, 0.0 to 1.0 (0.5 average). A distinct gift from
racecraft -- a great racer can still bog down. Feeds simulation._run_start.

Tyre management is how gently the rubber is used, 0.0 to 1.0 (0.5 neutral). High =
wears slower = longer stints. Decorrelated on purpose: some of the quickest, most
aggressive drivers are the hardest on their tyres. Feeds simulation._tyre_penalty.

Strategy is the head for the race, 0.0 to 1.0 (0.5 average). A high strategist
judges the tyre/pit trade clearly and lands on the optimal plan; a poor one
misjudges it and picks a worse one (wrong number of stops, wrong compounds). It
clouds plan selection in simulation._plan_strategy -- it does NOT make a slow car
fast, only a well-driven race well-judged. Also decorrelated: the fearless
chargers are often the worst planners.

All five axes are independent on purpose -- that's what makes a driver a character
rather than a single 'good/bad' dial.
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
    strategy: float = 0.5    # judgement of the tyre/pit plan, 0.0 to 1.0 -- higher picks better
    gender: str = "m"        # podium-voice casting only ("m"/"f"); default male, the women tagged below


GRID = [
    # Republic -- the ancients who'd burn the cave down
    Driver("Plato",                "Republic",      89.7, 0.15, 0.70, 0.55, 0.78, 0.80),  # the philosopher-king plans the ideal race and executes it
    Driver("Diogenes",             "Republic",      90.3, 0.32, 0.45, 0.72, 0.32, 0.18),  # the Cynic rejects all planning -- pure improvised chaos

    # Vanguard -- the revolutionaries
    Driver("Karl Marx",            "Vanguard",      90.0, 0.20, 0.55, 0.40, 0.82, 0.85),  # the long game incarnate: nurses the tyres and plans the grind to perfection
    Driver("Rosa Luxemburg",       "Vanguard",      89.9, 0.18, 0.75, 0.74, 0.60, 0.58, gender="f"),  # spontaneity over the master plan -- trusts the moment

    # Black Banner -- the anarchists
    Driver("Mikhail Bakunin",      "Black Banner",  89.8, 0.26, 0.80, 0.82, 0.30, 0.30),  # all-out charger: blistering, but no patience for a pit-wall plan
    Driver("Emma Goldman",         "Black Banner",  90.1, 0.21, 0.72, 0.75, 0.50, 0.52, gender="f"),  # fierce and fluent, but strategy is not her fight

    # Abyss -- the existentialists
    Driver("Friedrich Nietzsche",  "Abyss",         89.6, 0.22, 0.62, 0.70, 0.35, 0.42),  # will to power, not to spreadsheets: the quickest, the rashest gambler
    Driver("Simone de Beauvoir",   "Abyss",         89.9, 0.16, 0.82, 0.66, 0.82, 0.82, gender="f"),  # rigorous and systematic -- a plan as precise as her prose

    # Ends & Means -- the strategists
    Driver("Niccolò Machiavelli",  "Ends & Means",  90.2, 0.19, 0.92, 0.55, 0.88, 0.96),  # THE strategist: a slow car wielded with a cold, perfect race mind
    Driver("Richard Rorty",        "Ends & Means",  90.3, 0.18, 0.68, 0.62, 0.74, 0.72),  # the pragmatist: adaptable, sensible, rarely caught out

    # Frankfurt -- the critical theorists
    Driver("Theodor Adorno",       "Frankfurt",     90.4, 0.20, 0.66, 0.42, 0.58, 0.70),  # the analyst: sees the plan clearly, even if he despairs of it
    Driver("Herbert Marcuse",      "Frankfurt",     90.2, 0.23, 0.70, 0.70, 0.45, 0.55),  # the Great Refusal: attacks more than he plans

    # Différance -- the post-structuralists
    Driver("Michel Foucault",      "Différance",    90.0, 0.22, 0.74, 0.71, 0.68, 0.78),  # reads the whole board, finds the strategy nobody else saw
    Driver("Jacques Derrida",      "Différance",    90.5, 0.24, 0.71, 0.50, 0.55, 0.40),  # deconstructs the plan until there isn't one -- erratic by design

    # Liberation -- the anti-colonial radicals
    Driver("Frantz Fanon",         "Liberation",    90.1, 0.21, 0.78, 0.78, 0.48, 0.58),  # decisive in the moment, more tactician than strategist
    Driver("Aimé Césaire",         "Liberation",    90.4, 0.19, 0.69, 0.58, 0.66, 0.62),  # measured and composed, a tidy if unspectacular plan

    # Rights of Man -- the revolutionary pamphleteers
    Driver("Thomas Paine",         "Rights of Man", 90.3, 0.22, 0.67, 0.64, 0.62, 0.52),  # common sense over cunning -- a plain, honest strategy
    Driver("Mary Wollstonecraft",  "Rights of Man", 90.2, 0.18, 0.76, 0.66, 0.76, 0.74, gender="f"),  # rigorous and principled, a clear-eyed plan

    # Objectivism -- two individualists who will not yield, draft, or finish.
    # Racecraft 0.0: their philosophy IS their undoing. They retire every race.
    Driver("Ayn Rand",             "Objectivism",   90.6, 0.30, 0.00, 0.25, 0.20, 0.15, gender="f"),  # the pit wall is a collective; she will not be told when to stop
    Driver("Max Stirner",          "Objectivism",   90.7, 0.32, 0.00, 0.22, 0.20, 0.12),  # the egoist: a plan is just another spook to be ignored
]
