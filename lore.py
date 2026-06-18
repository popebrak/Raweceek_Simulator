"""The lore -- what the booth knows and how it riffs, as DATA the booth reasons over.

Like drivers.py and tracks.py, this file is pure data: no logic. The selection
engine (colour.py) reads these tables; it doesn't live here.

The unit is a Bit: a little chunk of broadcast, one or more TURNS of back-and-forth
between the two voices in the booth. Each turn is a (role, line) pair, where role
is "pbp" (the lap caller) or "colour" (his sidekick). A single dry one-liner from
the colour man is just a one-turn Bit; a proper exchange is several turns that
hand off between them -- which is what makes it sound like two people talking
rather than a database reciting facts.

Roles, not names: the lore never hardcodes "Vale" or "Benny". It says "pbp" and
"colour", and colour.py maps those to whoever is in the booth -- so renaming the
commentators (or swapping in a third) is a one-line change there, not a rewrite
here.

Lines are PROSE -- no numbers, no jargon -- because, like render_commentary, they
are written to be read aloud. And the colour man's job is to ENTERTAIN, not to
lecture: he wears the philosophy lightly, mostly to take the mickey out of it.

Five tables, most specific to most generic; the director prefers the rare gold and
falls back to filler when a cell is empty -- the usual dict.get(key, fallback). The
relational tables are SPARSE on purpose: only the pairings that actually sparkle.

  DRIVER_LORE        name             -> a driver's own character
  PAIR_LORE          (passer, passed) -> the history BETWEEN two drivers
  TEAM_LORE          team             -> a team's collective character
  TRACK_LORE         circuit          -> a circuit's own ghosts
  DRIVER_TRACK_LORE  (name, circuit)  -> what a driver MEANS at a given track

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
class Bit:
    """One chunk of broadcast: a tuple of (role, line) turns, a trigger, a weight."""
    turns: tuple
    when: str = "any"
    weight: int = 1


def quip(line, when="any", weight=1):
    """A single dry line from the colour man -- the common case."""
    return Bit((("colour", line),), when, weight)


def banter(turns, when="any", weight=1):
    """A multi-turn exchange. `turns` is a list of (role, line) pairs."""
    return Bit(tuple((r, l) for r, l in turns), when, weight)


# --- A driver's own character ------------------------------------------------
DRIVER_LORE = {
    "Plato": [
        quip("Plato out there chasing the perfect lap -- reckons there's an ideal one in another dimension and this is just the shadow of it."),
        quip("Leader Plato. Wants the wisest man to run everything. Funny how it's always the bloke saying it who volunteers.", when="leading"),
        quip("Designed the perfect society, that man. Can't perfectly negotiate a kerb, mind.", when="incident"),
    ],
    "Diogenes": [
        quip("Diogenes -- lived in a barrel, carried a lantern about in daylight looking for one honest man. He'll have more luck finding a clean overtake."),
        quip("Diogenes away well. Nothing to lose when all you own is a jar and an attitude.", when="start"),
        quip("No plan, no shame, no brakes. Living the dream, right up until the gravel.", when="incident"),
    ],
    "Karl Marx": [
        quip("Marx grinding it out -- the long game, always the long game. History's on his side, he'd tell you. History's not marshalling Turn 1, though."),
        quip("Marx leads. Spent years in a library working out how it all ends -- and, surprise, he reckons he wins.", when="leading"),
        quip("Stop for Marx, and you can bet there's a theory behind it. Even the tyre choice comes with a manifesto.", when="pit"),
    ],
    "Rosa Luxemburg": [
        quip("Luxemburg doesn't wait for the order -- just goes. Trusts the moment. Bit of a relief on a grid of overthinkers."),
        quip("Luxemburg in front on instinct alone. No committee, no memo, just sent it.", when="leading"),
    ],
    "Mikhail Bakunin": [
        quip("Bakunin out there -- wants to tear the whole thing down and see what grows back. Started with his own front wing, mostly."),
        quip("Bakunin attacks Turn 1 like it owes him money. The urge to destroy, he calls it. Creative, apparently.", when="start"),
        quip("Urge to destroy's a creative one, he says. Very creative with the barrier just then.", when="incident"),
    ],
    "Emma Goldman": [
        quip("Goldman -- said if she can't dance, it's not her revolution. She's dancing all over the kerbs, this one."),
        quip("Goldman leading and loving every second of it. Fierce, fast, answers to absolutely nobody.", when="leading"),
    ],
    "Friedrich Nietzsche": [
        quip("Nietzsche -- told everybody to live dangerously, and drives exactly like a man who took his own advice a shade too literally."),
        quip("Nietzsche leads. Not to win, he'd insist, but to overcome. From here it looks an awful lot like winning.", when="leading"),
        quip("Nietzsche living dangerously into Turn 1, as advertised.", when="start"),
        quip("Will to power, that. The will to understeer, more like.", when="incident"),
    ],
    "Simone de Beauvoir": [
        quip("de Beauvoir -- one isn't born quick, she'd say, one becomes quick. And she's become very quick indeed."),
        quip("de Beauvoir leads, every move deliberate. No bad faith, no wasted motion. Tidy as you like.", when="leading"),
    ],
    "Niccolò Machiavelli": [
        quip("Machiavelli wrote the book on getting power and keeping it -- and you can see him reading the race three corners ahead of everyone."),
        quip("Machiavelli out front. Rather be feared there than loved, and right now the whole field's terrified of his strategy.", when="leading"),
        quip("Machiavelli boxes -- exactly when it suits him and nobody else. The ends justify the in-lap.", when="pit"),
    ],
    "Richard Rorty": [
        quip("Rorty doesn't believe in grand truths, just whatever works. Pragmatist. Best sort of driver, honestly."),
        quip("Rorty leads with no theory at all -- whatever's working, he keeps doing it. Wish more of 'em thought like that.", when="leading"),
    ],
    "Theodor Adorno": [
        quip("Adorno reckons this whole circus is a machine for keeping us all docile. Entered it anyway. Make of that what you will."),
        quip("Adorno climbs out looking thoroughly vindicated. Happiest man in the paddock when it all goes wrong.", when="incident"),
    ],
    "Herbert Marcuse": [
        quip("Marcuse, the refusenik -- attacks first, asks questions never. Hero to every student who ever skipped a lecture to throw a brick."),
        quip("Marcuse off on the attack -- the Great Refusal, except he never once refuses a lunge.", when="start"),
    ],
    "Michel Foucault": [
        quip("Foucault sees control and power everywhere he looks. Probably thinks the pit limiter's a metaphor for something."),
        quip("Foucault leads, having found a line nobody else even noticed. Knowledge is power, and he's hoarding both.", when="leading"),
    ],
    "Jacques Derrida": [
        quip("Derrida could argue the finish line doesn't really exist. Be a brave moment to test that theory at the flag, mind."),
        quip("Derrida'd say the crash was always already happening. The marshals would say it's happening now.", when="incident"),
    ],
    "Frantz Fanon": [
        quip("Fanon diagnosed a whole empire and prescribed the cure. Doesn't wait for permission, this one."),
        quip("Fanon away decisively. Never did wait politely for an opening.", when="start"),
    ],
    "Aimé Césaire": [
        quip("Césaire -- the poet, the teacher. Half this grid would be lost without the words he gave them. Fanon especially."),
        quip("Césaire leads, composed as you like. The teacher quietly showing the class how it's done.", when="leading"),
    ],
    "Thomas Paine": [
        quip("Paine -- plain common sense, no cleverness. Lit two revolutions with a pamphlet and a clear sentence. Drives the same way."),
        quip("Paine out front on honest pace. No tricks. You sort of find yourself rooting for him.", when="leading"),
    ],
    "Mary Wollstonecraft": [
        quip("Wollstonecraft argued for half of humanity when the other half told her to sit down. Hasn't sat down since."),
        quip("Wollstonecraft leads on clear reason and nothing else. Exactly where she always said she'd be.", when="leading"),
    ],
    "Ayn Rand": [
        quip("Rand -- made selfishness a virtue and 'we' a swear word. Races for an audience of one. Herself."),
        quip("Rand won't yield, won't draft, won't give an inch -- nearly gave the whole lot away right there.", when="incident"),
        quip("And she's out. Wouldn't be told when to stop by the pit wall, so the wall told her instead.", when="retirement"),
    ],
    "Max Stirner": [
        quip("Stirner reckons every rule, every cause, every ideal is just a ghost in your head. The marshals are real enough, Max."),
        quip("Stirner bows to nothing. The laws of physics didn't get the memo.", when="incident"),
        quip("Stirner's gone. The pit plan was just another spook to him -- but a gravel trap's no ghost, mate.", when="retirement"),
    ],
}


# --- The history BETWEEN two drivers -----------------------------------------
# "overtake" Bits are DIRECTIONAL: the key is (passer, passed), and the lap caller
# has ALREADY called the pass -- so these turns are the REACTION, never a re-call.
# "rivalry" Bits read either way and surface when two rivals run nose-to-tail.
PAIR_LORE = {
    ("Friedrich Nietzsche", "Plato"): [
        banter([("colour", "Nietzsche past Plato -- spent his whole career calling the old man's perfect world a fairy story, and now he's binned him in the real one."),
                ("pbp", "Poetic justice, that?"),
                ("colour", "Poetic somethin'. All those Forms, and the only form that mattered was Nietzsche's braking point.")], when="overtake"),
        banter([("pbp", "Nietzsche right on the back of Plato here."),
                ("colour", "He'd love this. Reckoned the old man's whole philosophy was a comfort blanket for grown-ups -- now he wants the place to prove it.")], when="rivalry"),
    ],
    ("Plato", "Diogenes"): [
        banter([("colour", "Plato gets one back on Diogenes there."),
                ("pbp", "Didn't Diogenes make a fool of him once? Something with a chicken?"),
                ("colour", "Plucked one bare, held it up -- 'behold, Plato's man.' Brought the house down. Plato never forgot it, trust me.")], when="overtake"),
        banter([("pbp", "The Republic teammates, nose to tail."),
                ("colour", "Loftiest mind in history and the bloke who heckled him from a barrel. Same garage. Imagine those debriefs.")], when="rivalry"),
    ],
    ("Diogenes", "Plato"): [
        quip("Diogenes barges past Plato -- never had a scrap of respect for the man's lovely theories, and even less for his apex.", when="overtake"),
    ],
    ("Karl Marx", "Mikhail Bakunin"): [
        banter([("colour", "'Course Marx gets him -- had Bakunin chucked out the First International once, happy to do it again on track."),
                ("pbp", "Real bad blood, then."),
                ("colour", "The worst blood. Whole workers' movement split down the middle over these two, and now it's a braking duel into Turn 1.")], when="overtake"),
        banter([("pbp", "Marx and Bakunin, running together."),
                ("colour", "The authority man and the anarchist. Argued for years about who gets to give the orders. Neither's giving this corner up either.")], when="rivalry"),
    ],
    ("Mikhail Bakunin", "Karl Marx"): [
        quip("Bakunin past Marx! No gods, no masters, and absolutely no central committee telling him to hold position.", when="overtake"),
    ],
    ("Karl Marx", "Max Stirner"): [
        banter([("colour", "Marx past Stirner. He once wrote three hundred-odd pages just to tell this fella he was wrong."),
                ("pbp", "Three hundred pages?"),
                ("colour", "Took him one corner today. Should've led with that.")], when="overtake"),
    ],
    ("Karl Marx", "Rosa Luxemburg"): [
        banter([("pbp", "The Vanguard pair, together."),
                ("colour", "Comrades, those two -- though she always trusted the crowd where he trusted the plan. Friendly fire, this. Emphasis on the fire.")], when="rivalry"),
    ],
    ("Michel Foucault", "Jacques Derrida"): [
        banter([("colour", "These two fell out years ago -- over a book, would you believe."),
                ("pbp", "A book?"),
                ("colour", "A book. And Foucault's just done him round the outside. That'll be a footnote in the next one, that.")], when="overtake"),
        banter([("pbp", "Foucault and Derrida, line astern."),
                ("colour", "Closest they've been in years. Neither one of them will enjoy it one bit.")], when="rivalry"),
    ],
    ("Jacques Derrida", "Michel Foucault"): [
        quip("Derrida picks Foucault apart and slips through -- deconstructed the defence, you might say. He'd hate that I said that.", when="overtake"),
    ],
    ("Theodor Adorno", "Herbert Marcuse"): [
        quip("Adorno past Marcuse -- last time these two disagreed, one joined the students on the barricades and the other rang the police. I'll let you guess which.", when="overtake"),
        banter([("pbp", "The Frankfurt pair, together again."),
                ("colour", "Critical theory's odd couple. One wants the revolution, the other wants a quiet sit-down and a good cry about it.")], when="rivalry"),
    ],
    ("Frantz Fanon", "Aimé Césaire"): [
        banter([("colour", "Student past the teacher! Césaire taught Fanon damn near everything he knows."),
                ("pbp", "Not quite everything, clearly."),
                ("colour", "No -- didn't teach him to let the old man back through, did he.")], when="overtake"),
        banter([("pbp", "Fanon and Césaire, running as one."),
                ("colour", "Teacher and pupil. Lovely to see. Give it three laps and one of 'em outbrakes the other into oblivion.")], when="rivalry"),
    ],
    ("Thomas Paine", "Mary Wollstonecraft"): [
        quip("Paine edges past Wollstonecraft -- Rights of Man just ahead of the Rights of Woman. Same pub, same revolution, different pamphlet.", when="overtake"),
        banter([("pbp", "Paine and Wollstonecraft, together."),
                ("colour", "Drank in the same radical circles, these two. Every pamphlet they wrote put the wind up a king. Now they're scrapping over P-whatever.")], when="rivalry"),
    ],
    ("Mary Wollstonecraft", "Thomas Paine"): [
        quip("Wollstonecraft past Paine -- Rights of Woman ahead of Rights of Man, for once. About time, she'd say.", when="overtake"),
    ],
    ("Ayn Rand", "Karl Marx"): [
        quip("Rand past Marx -- capitalism over communism, and neither would lift for the other if you paid them. The whole twentieth century in one corner.", when="overtake"),
        banter([("pbp", "Rand and Marx, wheel to wheel."),
                ("colour", "There's your century, Vale. Not an inch given by either. I love it. Hate it. Bit of both, if I'm honest.")], when="rivalry"),
    ],
    ("Karl Marx", "Ayn Rand"): [
        quip("Marx past Rand -- the collective gets one over the great individualist. She'll be furious. Privately. Individually.", when="overtake"),
    ],
    ("Ayn Rand", "Max Stirner"): [
        banter([("pbp", "The Objectivism car -- Rand and Stirner."),
                ("colour", "Both worship the self. Difference is Rand had rules about it; Stirner thought rules were for ghosts. They'll both retire, mind. They always do.")], when="rivalry"),
    ],
    ("Simone de Beauvoir", "Mary Wollstonecraft"): [
        quip("de Beauvoir past Wollstonecraft -- two centuries apart, the same fight. The Second Sex sailing by the book that lit it.", when="overtake"),
        banter([("pbp", "de Beauvoir and Wollstonecraft, together on track."),
                ("colour", "Mother and heir of the whole argument, that. Two hundred years of it, right there in the gap to the car ahead.")], when="rivalry"),
    ],
    ("Friedrich Nietzsche", "Max Stirner"): [
        banter([("pbp", "Nietzsche and Stirner, close company."),
                ("colour", "Two egoists, each accused of nicking the other's homework. Neither one'll back off. Obviously.")], when="rivalry"),
    ],
    ("Niccolò Machiavelli", "Plato"): [
        quip("Machiavelli past Plato -- the realist past the dreamer. The Prince never did have much time for the perfect Republic.", when="overtake"),
        banter([("pbp", "Machiavelli stalking Plato."),
                ("colour", "Politics as it is, hunting politics as it ought to be. My money's on 'as it is.' Always is.")], when="rivalry"),
    ],
    ("Emma Goldman", "Mikhail Bakunin"): [
        banter([("pbp", "The Black Banner pair, together."),
                ("colour", "Goldman and Bakunin. No gods, no masters, no pit board. Thick as thieves and twice the trouble.")], when="rivalry"),
    ],
    ("Herbert Marcuse", "Karl Marx"): [
        quip("Marcuse on Marx's tail -- the student-movement hero chasing the old master whose book he waved at the barricades. Fanboy with a fast car.", when="rivalry"),
    ],
    ("Friedrich Nietzsche", "Simone de Beauvoir"): [
        banter([("pbp", "The Abyss teammates, nose to tail."),
                ("colour", "Stare into that gap long enough, Vale, and it stares back. Or you just close it. He'll close it.")], when="rivalry"),
    ],
}


# --- A team's collective character -------------------------------------------
TEAM_LORE = {
    "Republic": [banter([("pbp", "Tell us about the Republic pair, Benny."),
                         ("colour", "Plato and Diogenes. Founders of the whole game, can't agree on lunch. One wants to run a perfect city, the other lives in a barrel heckling him.")], when="any")],
    "Vanguard": [banter([("pbp", "Vanguard colours out there."),
                        ("colour", "Marx and Luxemburg. Here for the long game, history at their backs -- or so they keep telling the pit wall.")], when="any")],
    "Black Banner": [banter([("pbp", "The Black Banner squad."),
                            ("colour", "Bakunin and Goldman. No gods, no masters, and frankly no respect for a yellow flag. My kind of team. Nightmare to run.")], when="any")],
    "Abyss": [banter([("pbp", "The Abyss pair."),
                     ("colour", "Nietzsche and de Beauvoir. Reckon life comes with no instructions, so they drive like the manual's optional too.")], when="any")],
    "Ends & Means": [banter([("pbp", "Ends and Means."),
                            ("colour", "Machiavelli and Rorty. Whatever wins is, by their lights, the right thing to have done. Stewards can't stand 'em.")], when="any")],
    "Frankfurt": [banter([("pbp", "Frankfurt School colours."),
                         ("colour", "Adorno and Marcuse. Think the whole sport's a machine to keep us docile -- entered it anyway. Two seats, a full grid of irony.")], when="any")],
    "Différance": [banter([("pbp", "The Différance pair."),
                          ("colour", "Foucault and Derrida. For this lot nothing's fixed -- not truth, not meaning, probably not the classification. Timekeepers love that.")], when="any")],
    "Liberation": [banter([("pbp", "Liberation out there."),
                          ("colour", "Fanon and Césaire. The colony, come to race at the heart of the empire's favourite Sunday afternoon. Bit of poetry in that.")], when="any")],
    "Rights of Man": [banter([("pbp", "The Rights of Man pair."),
                             ("colour", "Paine and Wollstonecraft. Plain truth, equal rights, a pamphlet in each glovebox. Honest racers. Rare, that.")], when="any")],
    "Objectivism": [banter([("pbp", "And the Objectivism car."),
                           ("colour", "Rand and Stirner. Two egos, one rule: nobody tells me when to pit. They retire every single week, Vale. You could set your watch by it.")], when="any")],
}


# --- A circuit's own ghosts --------------------------------------------------
TRACK_LORE = {
    "Monza": [banter([("pbp", "Monza. The Temple of Speed."),
                     ("colour", "Oldest, fastest rhythm in the book. Big tow, late on the brakes, tifosi screaming for red. Can't not love it.")], when="any")],
    "Monte Carlo": [banter([("pbp", "Monte Carlo -- the jewel in the crown."),
                           ("colour", "And a fortress. Barriers an inch off your wheels, nowhere to pass, one mistake and your Sunday's done. Track position is everything here.")], when="any")],
    "Spa-Francorchamps": [banter([("pbp", "Spa-Francorchamps. Seven kilometres through the Ardennes."),
                                 ("colour", "Can be sunshine one end of the lap and biblical the other. And then there's Eau Rouge -- flat out, faithless, a proper leap of faith.")], when="any")],
    "Silverstone": [banter([("pbp", "Silverstone -- where it all began, back in 1950."),
                           ("colour", "Old wartime airfield, this. Maggotts and Becketts'll soon tell you who's actually brave and who just talks about it.")], when="any")],
    "Suzuka": [banter([("pbp", "Suzuka. The only figure-of-eight on the calendar."),
                      ("colour", "Crosses over itself, forgives nothing. Senna and Prost settled two titles here by parking it in each other. Lovely place.")], when="any")],
    "Interlagos": [banter([("pbp", "Interlagos. Short, anticlockwise, deafening."),
                          ("colour", "Senna's home crowd, this. Where championships come to die. More soul per metre than anywhere they go.")], when="any")],
}


# --- What a driver MEANS at a given track ------------------------------------
DRIVER_TRACK_LORE = {
    ("Karl Marx", "Monte Carlo"): [banter([("pbp", "Marx leading round the principality."),
                                          ("colour", "Round Monaco, of all places! Harbour full of yachts, bourgeoisie at brunch, and the one man alive who'd tax the lot of them out in front. He's grinding his teeth to dust.")], when="leading")],
    ("Diogenes", "Monte Carlo"): [quip("Diogenes in Monte Carlo -- a man who owned a barrel and a lantern, loose in the most expensive square mile on the planet. He thinks it's hilarious. So do I.", when="any")],
    ("Ayn Rand", "Monte Carlo"): [quip("Rand in Monaco, in her element -- a monument to money and achievement. About the one stop on the calendar she'd call beautiful.", when="any")],
    ("Friedrich Nietzsche", "Monte Carlo"): [quip("Nietzsche knows this coast -- wandered these hills working out how a man becomes what he is. Mostly he became a man who needed a good physio.", when="any")],
    ("Friedrich Nietzsche", "Spa-Francorchamps"): [quip("Eau Rouge for Nietzsche -- gaze long into a corner like that, he'd say, and it gazes back. Then you lift, and it wins.", when="any")],
    ("Karl Marx", "Silverstone"): [quip("Marx at Silverstone -- back on the island where he spent his exile, hunched in the British Museum taking capitalism apart a footnote at a time.", when="any")],
    ("Thomas Paine", "Silverstone"): [quip("Paine on home soil -- the Norfolk lad who lit two revolutions abroad and came home a heretic. Local hero, sort of. Depends who you ask.", when="any")],
    ("Mary Wollstonecraft", "Silverstone"): [quip("Wollstonecraft on English ground, where she argued for the other half of humanity against the entire weight of the age. And won, eventually.", when="any")],
    ("Frantz Fanon", "Interlagos"): [quip("Fanon at Interlagos -- fitting stage for the man who wrote the wretched of the earth right into the middle of the story.", when="any")],
}


# --- Last resort: there is always something to say ---------------------------
GENERIC = [
    banter([("pbp", "Twenty of the greatest minds in history, out on track."),
            ("colour", "And not one of 'em'll lift for another. Greatest minds in history, worst grid for sheer stubbornness I've ever called.")], when="any"),
    quip("Whole history of human thought out here, and they've agreed on exactly one thing: the racing line is mine.", when="any"),
    banter([("pbp", "Remarkable gathering of intellects, this grid."),
            ("colour", "Remarkable, yeah. Couldn't organise a pit stop between the lot of them, but remarkable.")], when="any"),
    quip("Every driver out here once told the others they were dead wrong. Nice they've finally got somewhere to settle it that isn't a footnote.", when="any"),
]


# --- Post-race podium quotes -- the DRIVERS speak, each in their own voice ----
# Used by the post-race show: the booth throws to the podium, and each finisher
# delivers a line that is unmistakably them. Keyed by name; missing names fall back.
PODIUM_QUOTES = {
    "Plato": ["The perfect race exists in a higher realm. Today I drove its shadow -- and the shadow was enough."],
    "Diogenes": ["I now own a barrel and a trophy. I shall be keeping the barrel."],
    "Karl Marx": ["The history of all racing is the history of strategy. Today, the strategy was correct."],
    "Rosa Luxemburg": ["I followed no master plan. The moment told me when to strike, and I listened."],
    "Mikhail Bakunin": ["I dismantled the field. The urge to destroy, as I have always said, is a creative one."],
    "Emma Goldman": ["If I cannot dance on the podium, I do not want it. ...I will, however, take the trophy."],
    "Friedrich Nietzsche": ["That which does not overtake me makes me stronger. I overtook all of them."],
    "Simone de Beauvoir": ["One is not born a winner. One becomes one -- braking point by braking point."],
    "Niccolò Machiavelli": ["It is better to be feared on the pit wall than loved. They feared my strategy, and rightly."],
    "Richard Rorty": ["There is no deep truth about who deserved this. There is only the timing screen, and I am atop it."],
    "Theodor Adorno": ["A victory under these conditions merely flatters the spectacle. ...It was, nonetheless, delightful."],
    "Herbert Marcuse": ["I refused to lift. The Great Refusal -- performed at two hundred miles an hour."],
    "Michel Foucault": ["Every driver out there was disciplined by the circuit. I disciplined the circuit."],
    "Jacques Derrida": ["There is no outside-the-podium. There is also, strictly, no podium. I won it regardless."],
    "Frantz Fanon": ["They built this sport to keep us out. Today the grid belonged to the excluded."],
    "Aimé Césaire": ["I gave a generation its words. Today I gave them the fastest lap as well."],
    "Thomas Paine": ["These are the laps that try drivers' souls. Plain courage won out, as it tends to."],
    "Mary Wollstonecraft": ["Let the record show: reason, not force, took this victory."],
}

PODIUM_QUOTE_FALLBACK = [
    "A good day's work. The arguments can wait until tomorrow.",
    "I will let the result speak. It is more eloquent than I am.",
]
