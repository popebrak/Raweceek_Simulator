"""The lore -- the colour analyst's knowledge, as DATA the booth reasons over.

Like drivers.py and tracks.py, this file is pure data: no logic lives here. The
selection engine (colour.py) reads these tables; it doesn't live here.

The unit is a Colour: one speakable line, plus a `when` tag saying WHICH on-track
moment it fits, plus a `weight` (higher = likelier to be chosen among equals).
Lines are PROSE -- no numbers, no jargon -- because, like render_commentary, they
are written to be read aloud.

Five tables, from the most specific to the most generic. The director prefers the
rare, specific gold (a genuine rivalry) and only falls back to filler when a cell
is empty -- the same `dict.get(key, fallback)` habit the rest of the project uses.
So the tables are SPARSE on purpose: there are 380 possible driver pairs and we
author only the dozen-odd that actually sparkle. That also makes this the safe,
fun file to expand -- anyone can drop in a witty line without touching the engine.

  DRIVER_LORE        name            -> a driver's own character
  PAIR_LORE          (passer, passed)-> the history BETWEEN two drivers
  TEAM_LORE          team            -> a team's collective character
  TRACK_LORE         circuit         -> a circuit's own ghosts and history
  DRIVER_TRACK_LORE  (name, circuit) -> what a driver MEANS at a given track

The `when` tags:
  "overtake"   a completed pass (PAIR_LORE here is DIRECTIONAL: first name passes)
  "rivalry"    two cars running nose-to-tail (PAIR_LORE here reads either way)
  "incident"   a mistake or spin
  "retirement" the car is out
  "start"      the lights-out charge to Turn 1
  "leading"    this driver is out front
  "any"        usable in any quiet moment -- the lull filler
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Colour:
    line: str
    when: str = "any"
    weight: int = 1


# --- A driver's own character ------------------------------------------------
DRIVER_LORE = {
    "Plato": [
        Colour("Plato out front, ruling from the ideal line -- the philosopher-king has a perfect Form of the lap in mind, and he is chasing it.", when="leading"),
        Colour("Plato, who dreamed up a Republic run by the wisest -- and quietly cast himself in the lead seat.", when="any"),
        Colour("even the architect of the ideal state can't legislate away a mistake -- the messy real world bites back.", when="incident"),
    ],
    "Diogenes": [
        Colour("Diogenes away like a man with nothing to lose -- which, owning only a barrel, he genuinely hasn't.", when="start"),
        Colour("Diogenes, the Cynic who lived in a clay jar and carried a lantern through daylight hunting one honest man -- good luck in this paddock.", when="any"),
        Colour("no plan, no shame, no brakes -- Diogenes racing exactly the way he lived.", when="incident"),
    ],
    "Karl Marx": [
        Colour("Marx in front, grinding out the long game -- history, he'd remind you, is on his side.", when="leading"),
        Colour("Marx, who spent his London exile hunched in the British Museum reading room, turning capital inside out.", when="any"),
        Colour("a coldly calculated stop from Marx -- the man never did anything without a theory of why.", when="pit"),
    ],
    "Rosa Luxemburg": [
        Colour("Luxemburg, who trusted the spontaneous surge of the crowd over any general's master plan -- and drives on pure instinct to match.", when="any"),
        Colour("Luxemburg leads on momentum alone -- no committee told her to; the moment simply arrived and she took it.", when="leading"),
    ],
    "Mikhail Bakunin": [
        Colour("Bakunin hurls it at the first corner as though the pit wall had personally insulted him -- the urge to destroy, he'd say, is a creative one.", when="start"),
        Colour("Bakunin, who'd tear the whole edifice down and trust whatever grows back -- subtlety was never the brief.", when="any"),
        Colour("Bakunin flings it at the scenery -- destruction always was more his medium than caution.", when="incident"),
    ],
    "Emma Goldman": [
        Colour("Goldman, who reckoned a revolution you can't dance to isn't worth having -- and races with exactly that joy.", when="any"),
        Colour("Goldman out front and relishing it -- fierce, fluent, and entirely her own woman.", when="leading"),
    ],
    "Friedrich Nietzsche": [
        Colour("Nietzsche leads -- not to finish, you understand, but to overcome. The will to power made flesh.", when="leading"),
        Colour("Nietzsche told us all to live dangerously, and there he goes proving it on the brakes into Turn 1.", when="start"),
        Colour("he gazed into the abyss once too often -- and this time the abyss gazed back.", when="incident"),
        Colour("Nietzsche, who pronounced God dead and then set about designing a man who wouldn't need one.", when="any"),
    ],
    "Simone de Beauvoir": [
        Colour("de Beauvoir, who taught that one is not born but becomes -- and has plainly become very, very quick.", when="any"),
        Colour("de Beauvoir leads with that rigorous, unhurried clarity -- every move chosen, nothing left to bad faith.", when="leading"),
    ],
    "Niccolò Machiavelli": [
        Colour("Machiavelli in front, and you sense he'd far rather be feared there than loved -- the cold, perfect race mind at work.", when="leading"),
        Colour("Machiavelli boxes the exact instant the cunning demands it -- with him the means always serve the end.", when="pit"),
        Colour("Machiavelli, who wrote the handbook on seizing power and keeping it, now quietly applying every page.", when="any"),
    ],
    "Richard Rorty": [
        Colour("Rorty, the ironist who thought truth was just what your peers let you get away with -- and races without a shred of dogma.", when="any"),
        Colour("Rorty leads, adaptable as ever -- no grand theory, simply whatever happens to be working today.", when="leading"),
    ],
    "Theodor Adorno": [
        Colour("Adorno, who'd call this whole glittering show the culture industry sedating the masses -- and is, awkwardly, entered in it.", when="any"),
        Colour("Adorno surveys the wreckage with a grim satisfaction -- he always suspected it would end this way.", when="incident"),
    ],
    "Herbert Marcuse": [
        Colour("Marcuse opens with the Great Refusal -- he attacks far more readily than he ever plans.", when="start"),
        Colour("Marcuse, darling of the student barricades, who saw refusal itself as the last truly free act.", when="any"),
    ],
    "Michel Foucault": [
        Colour("Foucault, who read every institution as a quiet machine of discipline -- and reads this circuit just as coldly.", when="any"),
        Colour("Foucault out front, having found the line of attack nobody else even saw -- knowledge is power, and he has both.", when="leading"),
    ],
    "Jacques Derrida": [
        Colour("Derrida, who'd deconstruct the very notion of a finish line until there wasn't one left to cross.", when="any"),
        Colour("the plan came apart in his hands -- though Derrida would insist it was always already coming apart.", when="incident"),
    ],
    "Frantz Fanon": [
        Colour("Fanon away decisively -- the man who theorised liberation never once waited politely for permission.", when="start"),
        Colour("Fanon, the psychiatrist who diagnosed a whole colonial world and prescribed its overthrow.", when="any"),
    ],
    "Aimé Césaire": [
        Colour("Césaire, poet of négritude, who taught a generation -- Fanon among them -- to name themselves before the empire could.", when="any"),
        Colour("Césaire leads, measured and composed -- the teacher showing the class precisely how it's done.", when="leading"),
    ],
    "Thomas Paine": [
        Colour("Paine, who turned plain common sense into a torch under two revolutions -- and drives just as plainly, just as hard.", when="any"),
        Colour("Paine out front on honest pace -- no cunning, no theory, just the rights of the matter.", when="leading"),
    ],
    "Mary Wollstonecraft": [
        Colour("Wollstonecraft, who vindicated the rights of woman when the whole age told her to sit down -- and never once did.", when="any"),
        Colour("Wollstonecraft leads on clear-eyed reason -- principled, rigorous, exactly where she argued she would be.", when="leading"),
    ],
    "Ayn Rand": [
        Colour("and there goes Rand -- the pit wall is a collective, and she will not be told when to stop. Her creed, as ever, is her undoing.", when="retirement"),
        Colour("Rand will not yield, will not draft, will not give an inch -- and very nearly hands the lot away here.", when="incident"),
        Colour("Rand, who made a virtue of selfishness and a villain of the word 'we' -- racing, fittingly, for an audience of one.", when="any"),
    ],
    "Max Stirner": [
        Colour("Stirner's out -- a pit plan, to the great egoist, was only ever another spook to be ignored. So he ignored it.", when="retirement"),
        Colour("Stirner bows to nothing, least of all a racing line -- and pays the egoist's price.", when="incident"),
        Colour("Stirner, for whom every cause, every ideal, every rule was a ghost haunting a mind that ought to own itself.", when="any"),
    ],
}


# --- The history BETWEEN two drivers -----------------------------------------
# "overtake" lines are DIRECTIONAL: the key is (passer, passed). "rivalry" lines
# read either way and surface when two rivals run nose-to-tail in a quiet spell.
PAIR_LORE = {
    ("Friedrich Nietzsche", "Plato"): [
        Colour("and THERE is the irony of the ages -- Nietzsche, who spent a lifetime dynamiting Plato's world of Forms, sweeps past the old idealist in the flesh!", when="overtake"),
        Colour("Nietzsche hunting Plato down -- the man who sneered that Christianity was just Platonism for the masses would dearly love this scalp.", when="rivalry"),
    ],
    ("Plato", "Diogenes"): [
        Colour("Plato past his own tormentor -- Diogenes once plucked a chicken and announced 'behold, Plato's man'; the master gets his answer here.", when="overtake"),
        Colour("Plato and Diogenes nose to tail -- the loftiest idealist in history, shadowed by the gadfly who mocked his every abstraction.", when="rivalry"),
    ],
    ("Diogenes", "Plato"): [
        Colour("Diogenes barges past Plato -- the Cynic never did have a shred of respect for the man's beautiful theories.", when="overtake"),
    ],
    ("Karl Marx", "Mikhail Bakunin"): [
        Colour("Marx past Bakunin -- the old First International feud rides again; he had the anarchist expelled once, and relishes doing it on track.", when="overtake"),
        Colour("Marx and Bakunin running together -- the authoritarian and the anarchist who tore the workers' movement in two over exactly this: who gets to give the orders.", when="rivalry"),
    ],
    ("Mikhail Bakunin", "Karl Marx"): [
        Colour("Bakunin lunges past Marx -- no gods, no masters, and certainly no central committee telling him to hold position.", when="overtake"),
    ],
    ("Karl Marx", "Max Stirner"): [
        Colour("Marx disposes of Stirner -- he once spent hundreds of furious pages demolishing 'Saint Max' in print; out here it takes a single corner.", when="overtake"),
        Colour("Marx shadowing Stirner -- the egoist who so needled him that he answered with a book-length demolition.", when="rivalry"),
    ],
    ("Karl Marx", "Rosa Luxemburg"): [
        Colour("the Vanguard pair together -- Marx and Luxemburg, comrades to the last, though she always trusted the crowd where he trusted the plan.", when="rivalry"),
    ],
    ("Michel Foucault", "Jacques Derrida"): [
        Colour("Foucault past Derrida -- and there's no love lost; their friendship died over a few pages on madness and never thawed.", when="overtake"),
        Colour("Foucault and Derrida together on track -- two titans of French theory who spent years in a frost neither would break.", when="rivalry"),
    ],
    ("Jacques Derrida", "Michel Foucault"): [
        Colour("Derrida deconstructs Foucault's defence and slips through -- the younger man who turned on his elder, doing it once again.", when="overtake"),
    ],
    ("Theodor Adorno", "Herbert Marcuse"): [
        Colour("Adorno past Marcuse -- the Frankfurt pair who split over the students of '68: Marcuse manned the barricades, Adorno called the police.", when="overtake"),
        Colour("Adorno and Marcuse side by side -- critical theory's odd couple, one cheering the revolution, the other quietly despairing of it.", when="rivalry"),
    ],
    ("Frantz Fanon", "Aimé Césaire"): [
        Colour("Fanon past Césaire -- the student overtaking his own teacher; it was Césaire who first taught him to refuse the colonizer's mirror.", when="overtake"),
        Colour("Fanon and Césaire together -- teacher and pupil, négritude and its fiercest young heir, running as one.", when="rivalry"),
    ],
    ("Thomas Paine", "Mary Wollstonecraft"): [
        Colour("Paine edges past Wollstonecraft -- two pamphleteers from the same revolutionary circle, the Rights of Man just ahead of the Rights of Woman.", when="overtake"),
        Colour("Paine and Wollstonecraft running together -- comrades in the same London radical set, each pamphlet shaking a throne.", when="rivalry"),
    ],
    ("Mary Wollstonecraft", "Thomas Paine"): [
        Colour("Wollstonecraft past Paine -- the Rights of Woman, for once, ahead of the Rights of Man.", when="overtake"),
    ],
    ("Ayn Rand", "Karl Marx"): [
        Colour("Rand past Marx -- there is no wider gulf on this grid; the apostle of selfishness ahead of the prophet of the collective.", when="overtake"),
        Colour("Rand and Marx wheel to wheel -- capitalism and communism made flesh, and neither will concede a single inch of tarmac.", when="rivalry"),
    ],
    ("Karl Marx", "Ayn Rand"): [
        Colour("Marx past Rand -- the collective, just this once, ahead of the individual who denied it even exists.", when="overtake"),
    ],
    ("Ayn Rand", "Max Stirner"): [
        Colour("the Objectivism pair together -- Rand and Stirner, both worship the self, though Rand was always horrified to be filed beside so lawless an egoist.", when="rivalry"),
    ],
    ("Simone de Beauvoir", "Mary Wollstonecraft"): [
        Colour("de Beauvoir past Wollstonecraft -- two centuries apart, the very same fight; the Second Sex sweeping by the Vindication that lit it.", when="overtake"),
        Colour("de Beauvoir and Wollstonecraft together -- the long arc of that argument made visible, the mother and the inheritor of modern feminism.", when="rivalry"),
    ],
    ("Friedrich Nietzsche", "Max Stirner"): [
        Colour("Nietzsche and Stirner running close -- the two great egoists, each accused of secretly inventing the other, neither bowing to a thing.", when="rivalry"),
    ],
    ("Niccolò Machiavelli", "Plato"): [
        Colour("Machiavelli past Plato -- the cold realist past the dreamer; The Prince never did have much patience for the Republic.", when="overtake"),
        Colour("Machiavelli stalking Plato -- politics as it actually is, hunting politics as it ought to be.", when="rivalry"),
    ],
    ("Emma Goldman", "Mikhail Bakunin"): [
        Colour("the Black Banner pair together -- Goldman and Bakunin, no gods and no masters, thick as anarchist thieves.", when="rivalry"),
    ],
    ("Herbert Marcuse", "Karl Marx"): [
        Colour("Marcuse on Marx's tail -- the New Left's hero chasing the old master whose work he carried to the barricades.", when="rivalry"),
    ],
    ("Friedrich Nietzsche", "Simone de Beauvoir"): [
        Colour("the Abyss teammates together -- Nietzsche and de Beauvoir, two who stared existence down and flatly refused to blink.", when="rivalry"),
    ],
}


# --- A team's collective character -------------------------------------------
TEAM_LORE = {
    "Republic": [Colour("the Republic pair -- Plato and Diogenes, the very bedrock of Western thought, who agree on absolutely nothing.", when="any")],
    "Vanguard": [Colour("Vanguard colours -- Marx and Luxemburg, here to win the long game with history at their backs.", when="any")],
    "Black Banner": [Colour("the Black Banner squad -- Bakunin and Goldman, no gods, no masters, and frankly little respect for the pit wall either.", when="any")],
    "Abyss": [Colour("the Abyss pair -- Nietzsche and de Beauvoir, who'd tell you existence arrives with no instructions, and you'd best drive like it.", when="any")],
    "Ends & Means": [Colour("Ends & Means -- Machiavelli and Rorty, the cold pragmatists; whatever wins is, by definition, the right thing to have done.", when="any")],
    "Frankfurt": [Colour("Frankfurt School colours -- Adorno and Marcuse, here under protest, suspicious of the very spectacle they're starring in.", when="any")],
    "Différance": [Colour("the Différance pair -- Foucault and Derrida, for whom nothing is ever fixed or quite what it claims, the leaderboard included.", when="any")],
    "Liberation": [Colour("Liberation colours -- Fanon and Césaire, the colony come to race at the very heart of the empire's favourite sport.", when="any")],
    "Rights of Man": [Colour("the Rights of Man pair -- Paine and Wollstonecraft, plain truth and equal rights, a pamphlet in each glovebox.", when="any")],
    "Objectivism": [Colour("Objectivism -- Rand and Stirner, the two great egoists, who would sooner retire than be told by anyone when to pit. And, reliably, do.", when="any")],
}


# --- A circuit's own ghosts and history --------------------------------------
TRACK_LORE = {
    "Monza": [
        Colour("Monza -- the Temple of Speed, where the old banking still curves up into the trees like a ghost, and the tifosi roar for red.", when="any"),
        Colour("the oldest, fastest rhythm in the sport -- Monza rewards the brave on the brakes and the braver in the tow.", when="any"),
    ],
    "Monte Carlo": [
        Colour("Monte Carlo -- run since 1929, the jewel in the crown, where the barriers sit inches away and a single error is the whole race.", when="any"),
        Colour("nowhere to pass and nowhere to hide -- the streets that made Senna look like a magician and everyone else merely mortal.", when="any"),
    ],
    "Spa-Francorchamps": [
        Colour("Spa -- seven kilometres through the Ardennes forest, where it can be sunlit at one end of the lap and pouring at the other.", when="any"),
        Colour("Eau Rouge and Raidillon ahead -- the most daunting sequence in the sport, flat-out and faithless, a leap you take on trust.", when="any"),
    ],
    "Silverstone": [
        Colour("Silverstone -- a wartime airfield that hosted the very first World Championship race back in 1950; this is where all of it began.", when="any"),
        Colour("Maggotts and Becketts coming up -- the fast, flowing test that separates the merely quick from the genuinely brave.", when="any"),
    ],
    "Suzuka": [
        Colour("Suzuka -- the only figure-of-eight on the calendar, a circuit that crosses over itself and forgives nothing.", when="any"),
        Colour("the ghosts of Senna and Prost still haunt these chicanes -- two title-deciders settled here by contact, a year apart.", when="any"),
    ],
    "Interlagos": [
        Colour("Interlagos -- short, anticlockwise and heaving with noise; Senna's home crowd, and the place where championships so often come to die.", when="any"),
        Colour("up and over through the Senna S -- a circuit with more soul per metre than almost anywhere they race.", when="any"),
    ],
}


# --- What a driver MEANS at a given track ------------------------------------
DRIVER_TRACK_LORE = {
    ("Karl Marx", "Monte Carlo"): [Colour("and isn't this the place for it -- Marx leading through Monte Carlo, the harbour bristling with yachts, capital's glittering shop window. You can almost hear him grinding his teeth.", when="leading"),
                                    Colour("Marx loose in Monte Carlo -- the harbour full of yachts, the bourgeoisie at play, the whole town a diorama of everything he spent his life indicting.", when="any")],
    ("Diogenes", "Monte Carlo"): [Colour("Diogenes here in Monte Carlo, of all places -- a man who owned a barrel and a lantern, turned loose among the most ostentatious wealth on earth.", when="any")],
    ("Ayn Rand", "Monte Carlo"): [Colour("Rand in her element at Monte Carlo -- a monument to wealth and achievement; about the one stop on the calendar she'd call beautiful.", when="any")],
    ("Friedrich Nietzsche", "Monte Carlo"): [Colour("fitting ground for Nietzsche, this coast -- he wandered these Riviera heights working out how a man might become what he is.", when="any")],
    ("Friedrich Nietzsche", "Spa-Francorchamps"): [Colour("Eau Rouge for Nietzsche -- gaze long enough into a corner like that, as he might say, and the corner gazes back into you.", when="any")],
    ("Karl Marx", "Silverstone"): [Colour("Marx at Silverstone -- back on the island where he spent his long exile, turning the engine of capital over in the British Museum.", when="any")],
    ("Thomas Paine", "Silverstone"): [Colour("Paine on home soil at Silverstone -- the Norfolk staymaker who lit two revolutions abroad before coming home a heretic.", when="any")],
    ("Mary Wollstonecraft", "Silverstone"): [Colour("Wollstonecraft at Silverstone, on English ground -- where she argued, against the entire weight of the age, for the other half of humanity.", when="any")],
    ("Frantz Fanon", "Interlagos"): [Colour("Fanon at Interlagos -- a fitting stage for the man who wrote the wretched of the earth into the very centre of history.", when="any")],
}


# --- Last resort: there is always something to say ---------------------------
GENERIC = [
    Colour("twenty of the most uncompromising minds in history, and not one of them was ever any good at yielding a corner.", when="any"),
    Colour("a grid that has argued about everything from the soul to the state -- and is now, briefly, only arguing about who's quickest.", when="any"),
    Colour("somewhere in the long history of thought, every driver here told the others they were wrong. Out on track they get to settle it.", when="any"),
    Colour("no agreement on this grid about truth, justice, or the good life -- but total consensus that the racing line belongs to them.", when="any"),
]
