"""The lore -- what the booth knows, as DATA the booth reasons over.

Like drivers.py and tracks.py, this file is pure data: no logic. The selection
engine (colour.py) reads these tables; it doesn't live here.

THE GUIDING PRINCIPLE -- THE RACING IS THE SHOW; THE PHILOSOPHY IS THE COLOUR.
When a line has to choose between calling the race and explaining an idea, it calls
the race. The ideas earn their place by illuminating what a driver is DOING out
there -- never by pausing the broadcast to deliver a seminar. Every authored line
here should pass one test: does it make the racing more vivid? If it only teaches
philosophy, it is in the wrong sport. The colour man wears the philosophy lightly --
he reaches for it to entertain, and he anchors it to the cars.

There are now THREE kinds of material, because a broadcast has more than one register:

  * THE CALLS -- the lap caller's factual lines: a pass, a crash, a getaway, a stop,
    an undercut. The booth owns these now (colour.py reads the pools below), just as
    it owns the colour man's reactions, so every word in the feed -- factual or wry --
    comes from one place and gets the same variety and no-repeat care.
        OVERTAKE_CALLS, START_CALLS, BATTLE_CALLS, SOLO_*, COLLISION_CALLS,
        PIT_CALLS, UNDERCUT_CALLS, plus CAUSE_PHRASE / SOLO_FLOURISH / CONTACT_WORD

  * EVENT REACTIONS -- short, punchy colour tied to a thing that just happened. These
    are `Bit`s: a `quip()` is one dry one-liner, a `banter()` is a quick exchange.
    They fire the instant the event does, as the REACTION to the call.
        DRIVER_LORE, PAIR_LORE, GENERIC_INCIDENT, GENERIC_OVERTAKE

  * DISCUSSIONS -- the quiet-lap conversation. A `Thread` is a DEVELOPED exchange,
    several turns long, that explores an idea THROUGH the racing (what the will to
    power looks like at the apex, why Marx and Bakunin can't share a corner, what Eau
    Rouge asks of a brave driver). The booth runs one a beat at a time across the
    green-flag laps, pausing when the racing interrupts -- and it prefers threads tied
    to a live battle over abstract ones, so the talk stays subordinate to the cars.
        DISCUSSIONS

Plus the bits the shows use: TRACK_LORE (the preview's quick scene-set), the podium
INTERVIEW (PODIUM_QUESTIONS / PODIUM_ANSWERS / PODIUM_QUOTES -- a real give-and-take,
racing first and the philosophy as the closing line).

Roles in every turn are "pbp" (the lap caller) and "colour" (his sidekick), plus
"report" (the pit-lane reporter, podium only) -- never hardcoded names, so colour.py
can recast the booth in one line. Lines are PROSE, no numbers, no jargon: they are
written to be read ALOUD (colour.py spells any number that survives into a line).
"""

from dataclasses import dataclass, field


# =============================================================================
# EVENT REACTIONS -- short, fired the instant something happens.
# =============================================================================

@dataclass(frozen=True)
class Bit:
    """One reaction: a tuple of (role, line) turns, a trigger tag, a weight."""
    turns: tuple
    when: str = "any"
    weight: int = 1


def quip(line, when="any", weight=1):
    """A single dry line from the colour man -- the common case."""
    return Bit((("colour", line),), when, weight)


def banter(turns, when="any", weight=1):
    """A short exchange. `turns` is a list of (role, line) pairs."""
    return Bit(tuple((r, l) for r, l in turns), when, weight)


# The `when` tags: "overtake", "incident", "retirement", "start", "any".
DRIVER_LORE = {
    "Plato": [
        quip("Even the architect of the perfect society can't legislate away a kerb.", when="incident"),
        quip("Plato away cleanly -- the philosopher-king takes the place that's his by right, he'd say.", when="start"),
    ],
    "Diogenes": [
        quip("Diogenes away like a man with nothing to lose -- which, owning a barrel, he hasn't.", when="start"),
        quip("No plan, no shame, no brakes. Living the dream, right up until the gravel.", when="incident"),
        quip("There it goes. The Cynic never did believe in the rules, including the ones holding the car on the road.", when="incident"),
    ],
    "Karl Marx": [
        quip("A calculated stop -- the man does nothing without a theory of why.", when="pit"),
    ],
    "Rosa Luxemburg": [
        quip("Luxemburg sends it -- didn't wait for the order, never does.", when="start"),
    ],
    "Mikhail Bakunin": [
        quip("Bakunin attacks Turn 1 like it owes him money. The urge to destroy, he calls it.", when="start"),
        quip("Urge to destroy's a creative one, he says. Very creative with the barrier just then.", when="incident"),
        quip("Down it goes. He always did prefer tearing things down to keeping them up.", when="incident"),
    ],
    "Emma Goldman": [
        quip("Goldman dances off the line -- if she can't enjoy the start, it's not her revolution.", when="start"),
    ],
    "Friedrich Nietzsche": [
        quip("Nietzsche living dangerously into Turn 1, as advertised.", when="start"),
        quip("Will to power, that. The will to understeer, more like.", when="incident"),
        quip("He gazed into the abyss once too often -- and this time it gazed back.", when="incident"),
    ],
    "Niccolò Machiavelli": [
        quip("Machiavelli boxes -- exactly when it suits him and nobody else. The ends justify the in-lap.", when="pit"),
    ],
    "Theodor Adorno": [
        quip("Adorno climbs out looking thoroughly vindicated. Happiest when it all goes wrong.", when="incident"),
    ],
    "Herbert Marcuse": [
        quip("Marcuse off on the attack -- the Great Refusal, except he never refuses a lunge.", when="start"),
    ],
    "Jacques Derrida": [
        quip("Derrida'd say the crash was always already happening. The marshals would say it's happening now.", when="incident"),
    ],
    "Frantz Fanon": [
        quip("Fanon away decisively -- never did wait politely for an opening.", when="start"),
    ],
    "Ayn Rand": [
        quip("Rand won't yield, won't draft, won't give an inch -- nearly gave the whole lot away there.", when="incident"),
        quip("And she's out. Wouldn't be told when to stop by the pit wall, so the wall told her instead.", when="retirement"),
    ],
    "Max Stirner": [
        quip("Stirner bows to nothing. The laws of physics didn't get the memo.", when="incident"),
        quip("Stirner's gone. The pit plan was just another spook to him -- but a gravel trap's no ghost, mate.", when="retirement"),
    ],
}

# Fallbacks so the colour man always has a fresh reaction, even for a driver with
# no line of their own -- variety without authoring a quip for all twenty per event.
GENERIC_INCIDENT = [
    quip("That's the trouble with being certain you're right -- the gravel doesn't read.", when="incident"),
    quip("Thinking too hard about the corner again. It doesn't care what you concluded.", when="incident"),
    quip("Every one of 'em reckons the laws of physics are up for debate. They are not.", when="incident"),
    quip("A brain that big, and still can't out-argue a kerb.", when="incident"),
    quip("A moment's doubt at this speed, and the scenery has its say.", when="incident"),
    quip("All that intellect, and the gravel still gets a vote.", when="incident"),
    quip("You cannot deduce your way out of a slide. Somebody ought to tell them.", when="incident"),
    quip("Certainty at two hundred miles an hour. What could possibly go wrong.", when="incident"),
    quip("There's a thesis in that mistake somewhere. Won't help him this afternoon.", when="incident"),
    quip("The mind says yes; the rear axle says absolutely not.", when="incident"),
    quip("Big ideas, small braking zone. The braking zone won.", when="incident"),
    quip("Genius is no defence whatsoever against a damp white line.", when="incident"),
    quip("Another one who confused being right with being grippy.", when="incident"),
    quip("That's what arguing with momentum gets you. It doesn't take questions.", when="incident"),
    quip("Every great thinker meets a problem they can't reason past. For this lot it's usually the wall.", when="incident"),
    quip("He had an answer for everything except the bit where the back end let go.", when="incident"),
    quip("Lovely theory of motion. Shame about the motion.", when="incident"),
]
GENERIC_OVERTAKE = [
    quip("Lovely move -- even the cleverest of 'em can't think their way out of being passed.", when="overtake"),
    quip("Down the inside and done. No theory required.", when="overtake"),
    quip("That's the thing about a good overtake: it ends the argument.", when="overtake"),
    quip("No footnotes, no caveats. Just gone.", when="overtake"),
    quip("He can write the rebuttal later. Right now he's second.", when="overtake"),
    quip("The cleanest argument there is: he's simply in front now.", when="overtake"),
    quip("Beautifully done. The other fellow can deconstruct it at his leisure.", when="overtake"),
    quip("Past -- and that is the end of THAT conversation.", when="overtake"),
    quip("A practical refutation. Nothing answers a clever man like a pass round the outside.", when="overtake"),
    quip("Theory's lovely. Track position's better.", when="overtake"),
    quip("Round the OUTSIDE -- some things you do, you don't sit and think about.", when="overtake"),
    quip("And the philosophy of the matter is: too slow.", when="overtake"),
    quip("Decided where every real argument gets decided -- the braking zone.", when="overtake"),
    quip("That's a sentence finished with a full stop. Goodnight.", when="overtake"),
]

# Occasional colour on a pit stop -- the strategic beat. Most stops pass without a
# word; now and then Benny has something dry to add about the gamble of it.
GENERIC_PIT = [
    quip("And there's the great leveller -- twenty-three seconds in the lane, and all that genius counts for nothing.", when="pit"),
    quip("The one decision out here that's pure cold maths. No amount of brilliance saves a stop a lap too late.", when="pit"),
    quip("Fresh rubber. Now we find out whether the plan was wisdom or wishful thinking.", when="pit"),
    quip("Track position handed over voluntarily. It takes nerve to give up the lead for a faster tomorrow.", when="pit"),
    quip("The pit wall speaks and they obey -- well, most of them. You know the two who won't.", when="pit"),
    quip("Lovely stop. The race is half-run in that lane, and nobody in the grandstand ever claps it.", when="pit"),
]


# =============================================================================
# THE CALLS -- the lap caller's FACTUAL lines, as data. Spoken prose; any number
# is spelled by colour.py before it airs. Placeholders: {driver}, {other},
# {at} (=" at <corner>" or ""), {pos} (a spelled ordinal -- "second"),
# {gained} (a spelled cardinal -- "four"), {stint} (spelled), {earlier}.
# Pools are deep and the booth never repeats one back-to-back, so the busiest
# afternoon of passing and stopping never reads from a script.
# =============================================================================

# Getaways off the line, by how big the launch was.
START_CALLS = {
    "lead": ["{driver} BEATS them all off the line -- leads into Turn 1!",
             "Lights out -- and it's {driver} who gets the jump to lead them away!",
             "A mighty launch from {driver} -- into Turn 1 with the lead!",
             "{driver} nails the start and sweeps into the lead at the first corner!"],
    "flier": ["{driver} -- what a launch! Storms up to {pos}!",
              "{driver} is away like a scalded cat -- up to {pos} already!",
              "Sensational getaway from {driver} -- {gained} places gained, up to {pos}!",
              "Where did {driver} come from?! A rocket off the line, up to {pos}!"],
    "good": ["{driver} gets a flier off the line, up to {pos}.",
             "Good launch from {driver} -- slots into {pos} through Turn 1.",
             "{driver} makes a couple off the start, up into {pos}.",
             "Tidy getaway, {driver} -- gains a place or two, up to {pos}."],
    "edge": ["{driver} edges ahead off the line, into {pos}.",
             "{driver} just noses into {pos} on the run down to Turn 1.",
             "A yard gained for {driver} -- into {pos}."],
}

# On-track passes for position, by what's at stake. The drama scales with the place.
OVERTAKE_CALLS = {
    "lead": ["{driver} sweeps past {other}{at} -- and takes the LEAD!",
             "{driver} is THROUGH on {other}{at} -- a new leader of this Grand Prix!",
             "There it is! {driver} dispatches {other}{at} to lead!",
             "{driver} makes it stick{at} -- past {other}, and into the lead!",
             "The move for the lead! {driver} clears {other}{at} and hits the front!"],
    "podium": ["{driver} forces it past {other}{at} for {pos}!",
               "{driver} dives past {other}{at} -- up to {pos}!",
               "Lovely move by {driver}{at}, clears {other} for {pos}!",
               "{driver} won't be denied{at} -- through on {other} for {pos}!",
               "{driver} has {other} for {pos}{at} -- and it's done cleanly!"],
    "points": ["{driver} gets the move done on {other}{at}, up to {pos}.",
               "{driver} picks off {other}{at} -- into {pos}.",
               "{driver} makes it past {other}{at} for {pos}.",
               "A place gained for {driver}{at}, ahead of {other} into {pos}.",
               "{driver} slots past {other}{at} and up to {pos}.",
               "{driver} finds a way by {other}{at} -- {pos} now."],
}

# A re-pass between two cars already scrapping -- collapse the flicker into one
# story. {driver} is whoever just went ahead; {pos} the place they're fighting over.
BATTLE_CALLS = {
    "again": ["...and {driver} fires straight back past {other}! They are TRADING this {pos} place!",
              "{driver} repays the compliment immediately -- back ahead of {other}! What a scrap!",
              "Side by side again -- and it's {driver} back in front of {other}! This is wonderful!",
              "Straight back through goes {driver}! These two are wheel to wheel for {pos}!"],
    "ongoing": ["...and AGAIN! {driver} ahead of {other} -- they have swapped this place more times than I can count!",
                "Still at it! {driver} edges back ahead -- {other} will have something to say next lap!",
                "{driver} leads this dance once more -- {other} right with them, glued to the gearbox!",
                "They are putting on a SHOW -- {driver} ahead of {other} again, and neither will yield!"],
}

# Solo errors -- a cause phrasing (CAUSE_PHRASE) plus, when the car survives, a
# severity flourish (SOLO_FLOURISH); when it ends the race, a retirement tag.
SOLO_RETIRE = ["{driver} {phrase}{at} -- a {severity} one, and THAT is the end of their race!",
               "{driver} {phrase}{at} -- and they're beached! Out of the Grand Prix!",
               "Disaster for {driver}, who {phrase}{at} -- their afternoon is OVER!",
               "{driver} {phrase}{at} -- no way back from that one. Retired."]

# The hopeless ones -- a car simply over its head (the Objectivism pair, every race).
OVERLIMIT_CALLS = ["{driver} is hopelessly out of their depth -- throws it away{at}, and OUT!",
                   "{driver} was never on terms with it -- bins it{at}, and that's their race run!",
                   "It was coming all along -- {driver} loses it{at} and is OUT of the Grand Prix!"]

# A delayed mechanical letting go from earlier damage.
DAMAGE_FAIL_CALLS = ["{driver}'s earlier damage finally lets go -- OUT OF THE RACE!",
                     "And there it is -- {driver}'s wounded car gives up the ghost. Retired.",
                     "The damage {driver} was carrying has done for them at last -- they're out."]

# Each cause carries SEVERAL phrasings -- the booth picks one and won't repeat it
# back-to-back. {at the corner} is appended by colour.py. (Moved here from display.py
# so the booth owns the words; display.py keeps only the timing-screen furniture.)
CAUSE_PHRASE = {
    "off-track": ["runs wide", "runs out of road", "sails off the circuit",
                  "drops it onto the run-off", "overcooks it and runs wide"],
    "lock-up":   ["locks up and runs deep", "flat-spots the fronts and skates wide",
                  "locks the inside front", "gets it all wrong under braking",
                  "lights up the fronts and sails on"],
    "spin":      ["spins it", "snaps round", "gets it all out of shape and spins",
                  "loses the rear and spins", "half-spins and scrabbles for grip"],
    "grass":     ["puts a wheel on the grass", "runs onto the green stuff and slithers",
                  "gets onto the marbles", "drops two wheels onto the grass",
                  "runs in too hot and onto the grass"],
    "kerb":      ["is launched over a sausage kerb", "clatters over the kerb",
                  "rides the kerb too hard and bounces wide", "gets the kerb all wrong",
                  "is fired skyward by the kerb"],
    "wall":      ["clips the wall", "brushes the barrier", "kisses the wall on the exit",
                  "glances off the barrier", "taps the wall"],
    "gravel":    ["digs into the gravel", "ploughs into the gravel trap",
                  "drops it into the gravel", "fishtails into the gravel",
                  "beaches a wheel in the gravel"],
}
# Severity, said the way a commentator would say it (no numbers) -- a pool each.
SOLO_FLOURISH = {
    "minor":    ["but gathers it up and carries on", "but catches it and continues",
                 "no harm done, they're still going", "but holds onto it, lucky"],
    "moderate": ["a scruffy moment, and that will have cost some time",
                 "untidy -- they'll have lost a chunk there",
                 "a real wobble, and time lost", "messy, and that hurts the lap"],
    "major":    ["a big one -- that could haunt the rest of their race",
                 "a huge moment -- lucky to still be running",
                 "an enormous error -- that will hurt", "a massive moment, and time torn up"],
}
CONTACT_WORD = {"minor": "light", "moderate": "firm", "major": "heavy"}

# Contact between two cars, by outcome. {driver} is the car that dived in; {other}
# the car defending; {word} the severity in plain English; {at} the corner.
COLLISION_CALLS = {
    "both_out": ["CONTACT{at}! {driver} and {other} collide -- a {severity} one, and they are BOTH OUT!",
                 "Oh, they've come together{at}! {driver} into {other} -- and that's the pair of them DONE!",
                 "Heavy contact{at}! {driver} and {other} take each other out of the Grand Prix!"],
    "other_out": ["{driver} dives down the inside of {other}{at} -- {other} is tipped into a spin and OUT, {driver} limps on!",
                  "{driver} lunges on {other}{at} -- and it's {other} who pays! Spun, and out of the race!",
                  "Contact{at}! {driver} survives it, but {other} is pitched out of the Grand Prix!"],
    "self_out": ["{driver} throws it up the inside of {other}{at} and comes off worst -- {driver} is OUT!",
                 "{driver} tries it on {other}{at}, gets it all wrong, and it's {driver} who's eliminated!",
                 "Ambitious from {driver}{at} -- too ambitious! {driver} bounces off {other} and OUT!"],
    "both_go": ["{driver} dives down the inside of {other}{at} -- side by side, {word} contact, and they BOTH keep going!",
                "Wheel to wheel{at}! {driver} and {other} touch -- {word} contact -- but away they both go!",
                "{driver} has a look at {other}{at} -- they bang wheels, {word} contact, no harm, racing on!"],
}

# Pit stops. {driver}, {stint} (spelled laps on the old set), {onto} (=" onto softs"
# or ""), {ord} (spelled stop number for repeat stops: "second").
PIT_CALLS = {
    "first": ["{driver} peels into the pit lane{onto}.",
              "And {driver} blinks first -- in they come{onto}.",
              "{driver} comes in to serve the stop{onto}.",
              "Box, box for {driver} -- in for service{onto}.",
              "{driver} dives into the lane after a {stint}-lap opening stint{onto}."],
    "again": ["{driver} is back in again{onto}.",
              "Another stop for {driver}{onto}.",
              "{driver} returns to the lane for the {ord} time{onto}.",
              "In comes {driver} once more{onto}.",
              "{driver} pits again after a {stint}-lap stint{onto}."],
}

# The undercut -- a pass won in the pit lane. {driver} undercutter, {other} victim,
# {earlier} ("a lap" / "three laps"), {pos} the place taken.
UNDERCUT_CALLS = {
    "lead": ["THE UNDERCUT IS ON FOR THE LEAD! {driver} stopped {earlier} earlier than {other} -- and has taken the lead in the pit lane!",
             "It's worked for the LEAD! {driver} boxed {earlier} before {other}, and the fresh rubber has done the rest -- {driver} leads!",
             "{driver} has stolen the lead in the pits! {earlier} earlier than {other}, and it's paid off completely!"],
    "points": ["THE UNDERCUT WORKS! {driver} boxed {earlier} earlier than {other}, and the fresh rubber vaults them up to {pos}.",
               "Strategy gold for {driver} -- in {earlier} before {other}, and they emerge ahead, up to {pos}.",
               "{driver} has done {other} in the pit lane -- {earlier} earlier on fresh tyres, and it's {pos} now.",
               "The undercut bites! {driver} stopped {earlier} sooner than {other} and jumps to {pos}."],
}


# Directional overtake reactions for the marquee pairings -- the lap caller has
# already called the pass; these are the booth's instant take on what it MEANS.
PAIR_LORE = {
    ("Friedrich Nietzsche", "Plato"): [
        banter([("colour", "Nietzsche past Plato -- spent his whole career calling the old man's perfect world a fairy story, and now he's binned him in the real one."),
                ("pbp", "Poetic justice?"),
                ("colour", "Poetic somethin'. The only Form that mattered was Nietzsche's braking point.")], when="overtake"),
    ],
    ("Plato", "Diogenes"): [
        banter([("colour", "Plato gets one back on Diogenes there."),
                ("pbp", "Didn't Diogenes make a fool of him with a chicken once?"),
                ("colour", "Plucked one bare -- 'behold, Plato's man.' The master's been waiting a long time to return that.")], when="overtake"),
    ],
    ("Diogenes", "Plato"): [
        quip("Diogenes barges past Plato -- never had a scrap of respect for the man's lovely theories, less for his apex.", when="overtake"),
    ],
    ("Karl Marx", "Mikhail Bakunin"): [
        banter([("colour", "'Course Marx gets him -- had Bakunin thrown out the First International once, happy to do it again on track."),
                ("pbp", "Bad blood."),
                ("colour", "The worst. The whole workers' movement split over these two, and it's still going at the Roggia.")], when="overtake"),
    ],
    ("Mikhail Bakunin", "Karl Marx"): [
        quip("Bakunin past Marx! No gods, no masters, and no central committee telling him to hold position.", when="overtake"),
    ],
    ("Karl Marx", "Max Stirner"): [
        banter([("colour", "Marx past Stirner. He once wrote three hundred pages just to tell this fella he was wrong."),
                ("pbp", "Three hundred?"),
                ("colour", "Took him one corner today. Should've led with that.")], when="overtake"),
    ],
    ("Michel Foucault", "Jacques Derrida"): [
        banter([("colour", "These two fell out years ago -- over a book, would you believe."),
                ("pbp", "A book?"),
                ("colour", "And now Foucault's done him round the outside. That'll be a footnote in the next one.")], when="overtake"),
    ],
    ("Jacques Derrida", "Michel Foucault"): [
        quip("Derrida picks Foucault apart and slips through -- deconstructed the defence, you might say. He'd hate that I said that.", when="overtake"),
    ],
    ("Theodor Adorno", "Herbert Marcuse"): [
        quip("Adorno past Marcuse -- last time they disagreed, one joined the students and the other rang the police. Guess which.", when="overtake"),
    ],
    ("Frantz Fanon", "Aimé Césaire"): [
        banter([("colour", "Student past the teacher! Césaire taught Fanon damn near everything he knows."),
                ("pbp", "Not quite everything."),
                ("colour", "No -- didn't teach him to let the old man back through.")], when="overtake"),
    ],
    ("Thomas Paine", "Mary Wollstonecraft"): [
        quip("Paine past Wollstonecraft -- Rights of Man just ahead of the Rights of Woman. Same revolution, different pamphlet.", when="overtake"),
    ],
    ("Mary Wollstonecraft", "Thomas Paine"): [
        quip("Wollstonecraft past Paine -- Rights of Woman ahead of Rights of Man, for once. About time, she'd say.", when="overtake"),
    ],
    ("Ayn Rand", "Karl Marx"): [
        quip("Rand past Marx -- the whole twentieth century in one corner, and neither would lift to save their life.", when="overtake"),
    ],
    ("Karl Marx", "Ayn Rand"): [
        quip("Marx past Rand -- the collective gets one over the great individualist. She'll be furious. Privately.", when="overtake"),
    ],
    ("Simone de Beauvoir", "Mary Wollstonecraft"): [
        quip("de Beauvoir past Wollstonecraft -- two centuries apart, the same fight, and the younger argument's ahead.", when="overtake"),
    ],
    ("Niccolò Machiavelli", "Plato"): [
        quip("Machiavelli past Plato -- the realist past the dreamer. The Prince never did have time for the Republic.", when="overtake"),
    ],
}


# =============================================================================
# DISCUSSIONS -- the quiet-lap conversation. Deep, multi-turn, run a beat at a
# time. `about` names the drivers a thread concerns (all must be running for it to
# be picked); `track` ties it to a circuit. Empty `about` = a general thread.
# =============================================================================

@dataclass(frozen=True)
class Thread:
    turns: tuple
    about: tuple = ()
    track: str = ""
    topic: str = ""


def discussion(turns, about=(), track="", topic=""):
    return Thread(tuple((r, l) for r, l in turns), tuple(about), track, topic)


DISCUSSIONS = [

    # --- single thinkers: what actually drives them ------------------------
    discussion([
        ("pbp", "For anyone new to this, Benny -- what actually drives Nietzsche out there?"),
        ("colour", "The will to power. And it's not what folk think -- it's not bossing people about."),
        ("pbp", "No?"),
        ("colour", "It's the drive in everything alive to grow, to overcome, to become MORE than it was. He'd say a tree doesn't grow to survive -- it grows to be a bigger tree."),
        ("pbp", "Which on a flying lap--"),
        ("colour", "--is a man never satisfied, always reaching past the limit. Thrilling to watch. Nightmare to put a delta time in front of."),
    ], about=("Friedrich Nietzsche",), topic="will to power"),

    discussion([
        ("pbp", "Marx sitting back early again."),
        ("colour", "Always does. His whole philosophy is that the big stuff -- who wins, who loses -- comes down to material conditions over time. Not heroics."),
        ("pbp", "The grand sweep of history."),
        ("colour", "He'd tell you the race is decided in the factory, not the cockpit. Tyres, fuel, the pit window. Bit cold -- but look at the order, he's usually right."),
    ], about=("Karl Marx",), topic="historical materialism"),

    discussion([
        ("pbp", "de Beauvoir, so precise out there."),
        ("colour", "She'd say you're not BORN a great driver -- you become one. Existence first, essence after. You make yourself, choice by choice."),
        ("pbp", "No excuses, then."),
        ("colour", "None. 'One is not born, but becomes' -- she meant it about being a woman, but it's every lap. Nobody hands you the racing line. You author it."),
    ], about=("Simone de Beauvoir",), topic="becoming"),

    discussion([
        ("pbp", "Diogenes is... a character."),
        ("colour", "Lived in a barrel. Owned a cup till he saw a child drink from cupped hands, then threw the cup away. Carried a lamp round in daylight 'looking for an honest man.'"),
        ("pbp", "Did he find one?"),
        ("colour", "Never. And his racecraft's the same -- no theory, just send it and embarrass the cleverer bloke. Told Alexander the Great once to get out of his light. To his face."),
    ], about=("Diogenes",), topic="the cynic"),

    discussion([
        ("pbp", "Machiavelli, reading the race three moves ahead as ever."),
        ("colour", "The original strategist. People hear 'Machiavellian' and think villain -- but he was just honest about how power actually works, not how we'd like it to."),
        ("pbp", "The ends justify the means."),
        ("colour", "More like: judge a leader by results, not intentions. That's the pit wall's creed exactly. He'd undercut his own grandmother and send a lovely card after."),
    ], about=("Niccolò Machiavelli",), topic="strategy"),

    discussion([
        ("pbp", "Foucault, finding lines nobody else sees."),
        ("colour", "He spent his life showing how power hides in the ordinary -- the timetable, the exam, the way a track quietly teaches you where you're 'allowed' to go."),
        ("pbp", "The panopticon."),
        ("colour", "A prison where you might always be watched, so you police yourself. He'd say the whole grid's been disciplined into the racing line -- then he goes and takes the one they trained everyone to avoid."),
    ], about=("Michel Foucault",), topic="discipline"),

    discussion([
        ("pbp", "Adorno doesn't look like he's enjoying the spectacle."),
        ("colour", "He never does. Coined 'the culture industry' -- mass entertainment that keeps us docile, sells the same thrill on a loop so we don't ask harder questions."),
        ("pbp", "So a Grand Prix is--"),
        ("colour", "--exhibit A. Bread and circuits. Mind you, this is the man who, when actual students occupied his lecture hall, called the police. Radical on paper, less so in the corridor."),
    ], about=("Theodor Adorno",), topic="culture industry"),

    discussion([
        ("pbp", "Plato out front, driving to some ideal."),
        ("colour", "Literally. He reckoned everything down here's a shadow of a perfect Form up in the realm of ideas -- a perfect circle, perfect justice, perfect lap."),
        ("pbp", "And the philosopher-king?"),
        ("colour", "His fix for politics: let the wisest rule. Funny how the man proposing it was always quite sure who the wisest was. Same energy as a driver certain the team should be built round him."),
    ], about=("Plato",), topic="the forms"),

    discussion([
        ("pbp", "Rand, refusing to yield as ever."),
        ("colour", "It's the whole philosophy. Objectivism -- the self is the only real thing, the collective's a lie. Rational self-interest, no apologies."),
        ("pbp", "Which on a race track--"),
        ("colour", "--means the pit wall can shout all it likes. 'Box now' is a committee giving HER orders. She'd sooner sit it out in the gravel a free woman than finish as somebody's instruction. And every week, she does."),
    ], about=("Ayn Rand",), topic="objectivism"),

    discussion([
        ("pbp", "Stirner -- never makes the flag, this one."),
        ("colour", "Course not. To Stirner every cause, every ideal, every duty is a 'spook' -- a ghost you let haunt you. Even Rand's principles were too much furniture for him."),
        ("pbp", "So a race plan--"),
        ("colour", "--is just another ghost. He owns himself, nothing owns him -- including the strategy that'd actually get him home. Marx wrote a whole book tearing him apart. Stirner barely noticed."),
    ], about=("Max Stirner",), topic="the ego and its own"),

    discussion([
        ("pbp", "Rorty -- no grand theory, just whatever works."),
        ("colour", "The ironist. Reckoned there's no Truth with a capital T waiting to be found -- just better and worse ways of talking, vocabularies we swap when they stop being useful."),
        ("pbp", "Sounds slippery."),
        ("colour", "Sounds slippery, drives sensible. No dogma to defend means nothing to be stubborn about. He'll bin a strategy the second it stops working -- which is exactly why he's so hard to catch out."),
    ], about=("Richard Rorty",), topic="pragmatism"),

    discussion([
        ("pbp", "Luxemburg, on instinct again."),
        ("colour", "Her great fight with the party men -- Lenin included. They wanted it all run from the top, one tight plan. She trusted the spontaneous action of the masses, the strike that starts itself."),
        ("pbp", "Freedom of the one who thinks differently."),
        ("colour", "That's her line. And it shows -- she doesn't wait for the pit wall. The gap opens, she's already through it."),
    ], about=("Rosa Luxemburg",), topic="spontaneity"),

    discussion([
        ("pbp", "Goldman, racing with such joy."),
        ("colour", "Deliberately. There's that line they hang on her -- if I can't dance, it's not my revolution. Whether she said it word for word or not, that's the spirit: liberation that forgets to enjoy itself isn't worth having."),
        ("pbp", "Anarchist to the core."),
        ("colour", "Through and through. No gods, no masters -- and no team order she's ever going to honour."),
    ], about=("Emma Goldman",), topic="anarchism"),

    discussion([
        ("pbp", "Paine, just honest pace, no tricks."),
        ("colour", "Common Sense -- the pamphlet that talked a colony into a revolution, in language a farmer could read at the kitchen table. No Latin, no cleverness. Just: this is daft, here's why."),
        ("pbp", "Plain-spoken."),
        ("colour", "Plainest on the grid. The others are deconstructing the racing line; Paine's just driving down it. Refreshing, honestly."),
    ], about=("Thomas Paine",), topic="common sense"),

    discussion([
        ("pbp", "Derrida -- what's he actually on about?"),
        ("colour", "Deconstruction. Take any neat opposition -- true and false, inside and outside -- and show it quietly undermines itself. Nothing means just one thing."),
        ("pbp", "And that drives how?"),
        ("colour", "Erratically! No fixed plan, because for him there's no fixed anything. Talks himself out of the obvious line into something nobody saw -- sometimes genius, sometimes the gravel."),
    ], about=("Jacques Derrida",), topic="deconstruction"),

    discussion([
        ("pbp", "Marcuse, attacking from the off."),
        ("colour", "The Great Refusal -- his idea that the last free act left, in a system that's bought everyone off, is simply to say no. Refuse to play along."),
        ("pbp", "Hero to the students."),
        ("colour", "Their philosopher-king in '68. One-Dimensional Man on every barricade. And it shows -- he doesn't manage a race, he refuses to lift."),
    ], about=("Herbert Marcuse",), topic="the great refusal"),

    discussion([
        ("pbp", "Bakunin -- all-out from lights to flag."),
        ("colour", "His one line that everybody knows: the urge to destroy is a creative urge. He meant tear down the old order and trust what grows back."),
        ("pbp", "Bit of a gamble."),
        ("colour", "Whole career was. No blueprint, no transitional plan, just burn it down and have faith. Marvellous to watch. You wouldn't lend him your car."),
    ], about=("Mikhail Bakunin",), topic="destruction"),

    discussion([
        ("pbp", "Wollstonecraft, picking the field off one by one."),
        ("colour", "And there's her whole argument, made visible. Give a driver reason and a fair shot, she said, and watch what they do -- it's the ones who assumed she couldn't who look daft from back here."),
        ("pbp", "Rights of Woman."),
        ("colour", "Two hundred years early, and they mocked it. Hard to mock from her mirrors, mind. The case rather makes itself at this speed."),
    ], about=("Mary Wollstonecraft",), topic="rights of woman"),

    discussion([
        ("pbp", "Césaire -- the poet on the grid, and it shows in how he drives."),
        ("colour", "It does. Measured, composed, every input placed like a word in a line. The flashier lads are throwing the car at the corner; Césaire's writing his lap out longhand, and it's quicker than it looks."),
        ("pbp", "Nothing wasted."),
        ("colour", "Not a movement. Négritude was his -- take the identity they tried to shame out of you and wear it with pride -- and he races like a man with nothing left to apologise for. Composed all the way down."),
    ], about=("Aimé Césaire",), topic="negritude"),

    discussion([
        ("pbp", "Fanon, decisive -- never seems to hesitate."),
        ("colour", "Never. Watch him into a corner: committed before the others have finished thinking. He argued the wretched of the earth don't WAIT to be granted freedom -- they take it."),
        ("pbp", "And out here?"),
        ("colour", "Same man. He doesn't ask the car ahead for permission, because he never asked anyone for anything. See a gap, take a gap. A whole philosophy of liberation, run flat out."),
    ], about=("Frantz Fanon",), topic="liberation"),

    # --- rivalries: the history between two ---------------------------------
    discussion([
        ("pbp", "There's real needle between Nietzsche and Plato, isn't there."),
        ("colour", "Two and a half thousand years of it. Plato reckoned the real world's a pale copy of a perfect one -- the Forms, up in the realm of ideas."),
        ("pbp", "And Nietzsche?"),
        ("colour", "Thought that was the biggest con in history. Inventing a 'true world' somewhere else just to run down the only one we've got. Called Christianity 'Platonism for the people' -- same trick, bigger congregation."),
        ("pbp", "So when he hunts Plato down--"),
        ("colour", "--it's not a pass, it's a verdict. The real world going past the dream of a better one."),
    ], about=("Friedrich Nietzsche", "Plato"), topic="nietzsche vs plato"),

    discussion([
        ("pbp", "The needle between Marx and Bakunin goes back a long way."),
        ("colour", "The First International. Workers of the world finally organised -- and these two couldn't share a committee."),
        ("pbp", "Over what?"),
        ("colour", "Authority. Marx wanted a disciplined party to seize the state. Bakunin wanted no state at all -- said any new boss is still a boss. Marx had him expelled; Bakunin called him a tyrant in waiting."),
        ("pbp", "So side by side here--"),
        ("colour", "--that's not teammates squabbling. That's the whole argument about how you change the world, settled at the Roggia."),
    ], about=("Karl Marx", "Mikhail Bakunin"), topic="marx vs bakunin"),

    discussion([
        ("pbp", "Adorno and Marcuse -- the Frankfurt pair, but not always on the same page."),
        ("colour", "Sixty-eight split them clean down the middle. The students rose up, and Marcuse was out there with them -- became the grandfather of the New Left."),
        ("pbp", "And Adorno?"),
        ("colour", "Called the police on the ones who occupied his institute. Marcuse wrote to him, basically: how can YOU, of all people? Two old comrades, and the revolution they'd theorised showed up and they couldn't agree whether to open the door."),
    ], about=("Theodor Adorno", "Herbert Marcuse"), topic="frankfurt split"),

    discussion([
        ("pbp", "Fanon and Césaire -- there's a lineage there."),
        ("colour", "Césaire taught the young Fanon in Martinique. Gave him négritude -- reclaim the identity the empire tried to shame out of you, wear it with pride."),
        ("pbp", "And Fanon took it further."),
        ("colour", "All the way to liberation -- the wretched of the earth throwing off the whole setup, by force if need be. The student outgrew the teacher. Happens. Doesn't mean he'll let him back through."),
    ], about=("Frantz Fanon", "Aimé Césaire"), topic="fanon and cesaire"),

    discussion([
        ("pbp", "Wollstonecraft and de Beauvoir, two hundred years apart."),
        ("colour", "Same fight, different century. Wollstonecraft in 1792, vindicating the rights of woman when the whole age said sit down and look pretty."),
        ("pbp", "And de Beauvoir picked up the baton."),
        ("colour", "The Second Sex, a century and a half on -- showed how 'woman' gets made into the 'other.' Draw a straight line from one to the other. Tonight it's a straight line through the field, the pair of them."),
    ], about=("Mary Wollstonecraft", "Simone de Beauvoir"), topic="feminism across centuries"),

    discussion([
        ("pbp", "Foucault and Derrida running together -- there's history."),
        ("colour", "Once close, then a proper falling-out. Derrida wrote a savage critique of one of Foucault's books, on madness, and the friendship never recovered. Years of frost."),
        ("pbp", "Two giants of French theory."),
        ("colour", "And neither would give the other a thing. Including, by the look of it, this corner."),
    ], about=("Michel Foucault", "Jacques Derrida"), topic="foucault vs derrida"),

    discussion([
        ("pbp", "Rand and Marx, wheel to wheel -- you couldn't write it."),
        ("colour", "The widest gulf in the history of ideas, that. The apostle of the self versus the prophet of the collective. Everything one believes, the other calls a disease."),
        ("pbp", "No love lost."),
        ("colour", "None possible. And neither will lift -- because lifting, to both of them, would mean the other was right about something. They'll crash before they concede.")
    ], about=("Karl Marx", "Ayn Rand"), topic="marx vs rand"),

    discussion([
        ("pbp", "Marx shadowing Stirner here."),
        ("colour", "The egoist who got right under his skin. Stirner said every ideal -- including Marx's beloved 'humanity' -- was a spook, a fiction."),
        ("pbp", "And Marx's reply?"),
        ("colour", "Three hundred-odd pages of it. 'Saint Max,' he called him, sarcastically, for chapter after chapter. You don't write that much about someone you're not rattled by.")
    ], about=("Karl Marx", "Max Stirner"), topic="marx vs stirner"),

    discussion([
        ("pbp", "The Objectivism pair, Rand and Stirner -- two of a kind?"),
        ("colour", "Both worship the self, but they can't stand each other really. Rand built rules around her egoism -- reason, rights, a whole system."),
        ("pbp", "And Stirner?"),
        ("colour", "Thought rules were for ghosts. No system, no morality, nothing sacred but himself. Rand was horrified to be filed next to him. Two self-made men, neither will finish. Poetic, that.")
    ], about=("Ayn Rand", "Max Stirner"), topic="the egoists"),

    discussion([
        ("pbp", "Plato and Diogenes -- the same garage, somehow."),
        ("colour", "Loftiest mind in history, and the man who heckled him from a barrel. Plato builds a perfect city in his head; Diogenes wanders the actual one with a lamp calling everyone frauds."),
        ("pbp", "They genuinely clashed."),
        ("colour", "Constantly. Plato called Diogenes 'a Socrates gone mad.' Diogenes called Plato a show-off with nice furniture. Imagine those two on the same pit wall.")
    ], about=("Plato", "Diogenes"), topic="republic teammates"),

    discussion([
        ("pbp", "Bakunin and Goldman -- the Black Banner pair."),
        ("colour", "Kindred spirits, these two. Both anarchists, both no gods no masters -- but where Bakunin's all fire and dynamite, Goldman brought the heart. Free speech, free love, the joy of it."),
        ("pbp", "A double act."),
        ("colour", "The best kind. Thick as thieves, and twice the trouble for any pit wall trying to tell them anything.")
    ], about=("Mikhail Bakunin", "Emma Goldman"), topic="black banner"),

    # --- a thinker AND this circuit ----------------------------------------
    discussion([
        ("pbp", "And of all the places to bring Karl Marx -- Monte Carlo."),
        ("colour", "Ha! The man wrote a thousand pages on capital, and here he is doing laps past the superyachts."),
        ("pbp", "He must hate it."),
        ("colour", "Loves it and hates it. It's his thesis made of fibreglass and champagne -- the harbour's basically Chapter One of Capital with a marina. Every lap's a lecture he can't give."),
    ], about=("Karl Marx",), track="Monte Carlo", topic="marx at monaco"),

    discussion([
        ("pbp", "Eau Rouge coming up -- and Nietzsche's the man for it."),
        ("colour", "Made for him, that corner. Uphill, blind, a genuine act of faith at the top. Gaze long into it, he'd say, and it gazes back."),
        ("pbp", "Live dangerously."),
        ("colour", "His whole creed in one corner. The brave go flat and find out who they are. The sensible lift and stay who they were."),
    ], about=("Friedrich Nietzsche",), track="Spa-Francorchamps", topic="nietzsche at spa"),

    discussion([
        ("pbp", "Diogenes here in Monte Carlo, of all places."),
        ("colour", "A man who owned a barrel and a lamp, loose in the most expensive square mile on the planet. He thinks it's hilarious."),
        ("pbp", "So do you."),
        ("colour", "So do I. He spent his life calling wealth a sickness -- and they've parked a billion quid of boats right where he can see them. He's having the time of his afterlife.")
    ], about=("Diogenes",), track="Monte Carlo", topic="diogenes at monaco"),

    # --- the circuit itself -------------------------------------------------
    discussion([
        ("pbp", "Monza -- the Temple of Speed."),
        ("colour", "Fastest place they race. Used to have the old banking -- this great concrete wall of a curve up in the trees. Stopped using it because it was trying to kill people, but it's still up there, watching."),
        ("pbp", "And the tifosi."),
        ("colour", "Loudest crowd in the sport, and they love exactly one colour. Win here in red and you're a god. Win in anything else and you've spoiled their afternoon."),
    ], track="Monza", topic="monza"),

    discussion([
        ("pbp", "Monte Carlo -- the jewel in the crown."),
        ("colour", "And the hardest place on earth to pass. Barriers where the run-off should be. They've raced here since 1929 and the track's barely changed -- you can't widen a principality."),
        ("pbp", "Track position everything."),
        ("colour", "Qualifying's the whole game. Senna round here was something not quite human. Everyone else just tries not to bin it for two hours and calls it a result."),
    ], track="Monte Carlo", topic="monaco"),

    discussion([
        ("pbp", "Spa -- seven kilometres through the Ardennes forest."),
        ("colour", "A proper old monster. Long enough it can be bone dry at one end of the lap and chucking it down at the other. Genuinely, same lap."),
        ("pbp", "Drivers love it."),
        ("colour", "To a soul. It's the one they'd all keep if you took the rest away. You earn a lap of Spa -- it doesn't give you a thing."),
    ], track="Spa-Francorchamps", topic="spa"),

    discussion([
        ("pbp", "Silverstone -- where the whole world championship began, back in 1950."),
        ("colour", "Old bomber airfield, this. You can still feel the runways in the layout. And then Maggotts and Becketts -- that fast left-right-left-right that sorts the brave from the bragging."),
        ("pbp", "Quick corners."),
        ("colour", "The quickest. Get them right and it's the best feeling in the sport. Get them wrong and it's a very long walk back."),
    ], track="Silverstone", topic="silverstone"),

    discussion([
        ("pbp", "Suzuka -- the only figure-of-eight they race."),
        ("colour", "Crosses over itself on a bridge. Honda built it as a test track and somehow made the best circuit in the world by accident."),
        ("pbp", "It has history."),
        ("colour", "Senna and Prost settled two championships here by driving into each other, one year apart. Hallowed ground. Slightly haunted ground."),
    ], track="Suzuka", topic="suzuka"),

    discussion([
        ("pbp", "Interlagos -- short, anticlockwise, and absolutely heaving."),
        ("colour", "Senna's home. The crowd here doesn't watch a race, it has a religious experience. Bumpy old place on a hillside, runs the wrong way round--"),
        ("pbp", "And the championships."),
        ("colour", "Keep coming down to the last lap here. Something in the water. Magic, this place. Pure magic."),
    ], track="Interlagos", topic="interlagos"),

    # --- general: the philosophy and the racing ----------------------------
    discussion([
        ("pbp", "It's a strange grid, this -- the whole history of thought, in cars."),
        ("colour", "And every one of them dead certain the others are wrong. Twenty people who built their lives on never backing down, all asked to share one corner."),
        ("pbp", "What could go wrong."),
        ("colour", "Everything, ideally. That's why we get up in the morning, Vale."),
    ], topic="the grid"),

    discussion([
        ("pbp", "Does any of the philosophy actually help them drive, Benny?"),
        ("colour", "Honestly? The ones who win are the ones who stop philosophising at the white line."),
        ("pbp", "Go on."),
        ("colour", "Think too hard about whether the corner 'really' exists, and you'll be in the wall while you're still deciding. Out here, the deepest thought is: brake later."),
    ], topic="does it help"),

    discussion([
        ("pbp", "You've called a lot of grids. How's this one compare?"),
        ("colour", "Cleverest field I've ever seen. Worst I've ever seen at being told anything."),
        ("pbp", "Ha."),
        ("colour", "You don't coach this lot. You point them at Turn 1, wish them luck, and take cover behind the pit wall."),
    ], topic="cleverest field"),

    # --- second angles: more on each thinker, so no driver is a one-note act ----
    discussion([
        ("pbp", "Benny, the eternal recurrence -- Nietzsche's strangest idea."),
        ("colour", "A thought experiment. What if you had to live this exact life -- this exact race, every mistake, every triumph -- over and over, forever?"),
        ("pbp", "Cheerful."),
        ("colour", "His test was: could you say YES to that? Love it so fiercely you'd take it on a loop? He drives like a man who would. Same corner, same total commitment, every single time."),
    ], about=("Friedrich Nietzsche",), topic="eternal recurrence"),

    discussion([
        ("pbp", "'God is dead' -- the line everyone knows."),
        ("colour", "And everyone misreads. He wasn't cheering. He meant we'd killed off the old certainties, and now we had to invent our own meaning. Terrifying, not triumphant."),
        ("pbp", "So out there--"),
        ("colour", "--no rulebook from on high tells him the line. He decides what's worth doing at two hundred miles an hour, and lives with it. Or doesn't."),
    ], about=("Friedrich Nietzsche",), topic="god is dead"),

    discussion([
        ("pbp", "Marx talks about alienation. What's he getting at?"),
        ("colour", "The worker who builds the thing but owns none of it -- recognises nothing of himself in what he made. Modern work, Marx reckoned, cuts you off from your own hands."),
        ("pbp", "And a racing driver?"),
        ("colour", "Funny case. It's all him out there, no production line. Marx might call him the least alienated man on the grid -- then ruin the compliment by asking who owns the team."),
    ], about=("Karl Marx",), topic="alienation"),

    discussion([
        ("pbp", "'Religion is the opium of the people' -- Marx again."),
        ("colour", "Less of a sneer than it sounds. Opium was the painkiller of the age. He meant it numbs a real pain -- gives comfort while the cause of the suffering stays put."),
        ("pbp", "And eighty thousand roaring fans?"),
        ("colour", "Same family, he'd say. Glorious distraction. All that feeling, shared, enormous -- and not one of them thinking about the price of the ticket."),
    ], about=("Karl Marx",), topic="opium of the people"),

    discussion([
        ("pbp", "The allegory of the cave, Benny. Give us it."),
        ("colour", "Prisoners chained facing a wall, watching shadows, certain the shadows are the world. One breaks free, sees the sun, comes back to tell them -- and they decide he's mad."),
        ("pbp", "Bleak."),
        ("colour", "That's Plato's whole game: most people mistake the shadow for the thing. Half this grid's chasing the reflection of a perfect lap they've half-glimpsed. He thinks he's chasing the real one."),
    ], about=("Plato",), topic="the cave"),

    discussion([
        ("pbp", "There's a chariot in Plato somewhere, isn't there?"),
        ("colour", "The soul as a charioteer with two horses -- one noble, one wild -- and the whole art of living is keeping the pair pulling as one."),
        ("pbp", "That's just car control."),
        ("colour", "It IS car control. Reason holding appetite and temper on a single line. Lose the wild horse and you're in the barrier. He wrote a setup guide two thousand years early."),
    ], about=("Plato",), topic="the chariot"),

    discussion([
        ("pbp", "de Beauvoir, so precise through here."),
        ("colour", "Surgical. And it's no accident -- her whole method was to refuse the comfortable story and look hard at what's actually in front of you. No flinching, no flattering yourself."),
        ("pbp", "You can see it in the car."),
        ("colour", "Every lap. She doesn't drive the corner she WISHES was there -- she drives the one that is. Brakes where the grip really ends, not where pride says it should. That clear eye on reality is worth half a second."),
    ], about=("Simone de Beauvoir",), topic="clear sight"),

    discussion([
        ("pbp", "Machiavelli on fortune -- 'fortuna,' he called it."),
        ("colour", "Half of life's luck, he reckoned. Fortuna, a river that floods when it pleases. The other half's virtu -- the skill and the nerve to build your banks before it does."),
        ("pbp", "So when it rains--"),
        ("colour", "--fortuna's having her say. And the man who read the sky, who had the inters ready -- that's virtu. He'd adore a wet race. It's his entire theory, made visible."),
    ], about=("Niccolò Machiavelli",), topic="fortune and virtue"),

    discussion([
        ("pbp", "Foucault wrote about prisons, hospitals, asylums..."),
        ("colour", "All the places that measure you, sort you, correct you. He showed modern power doesn't take your head -- it weighs you, files you, optimises you."),
        ("pbp", "Like a data engineer."),
        ("colour", "Exactly like a data engineer. Every sector time, every input, every heartbeat logged. He saw it coming. He'd call the telemetry screen the most honest object in the paddock."),
    ], about=("Michel Foucault",), topic="biopower"),

    discussion([
        ("pbp", "Rorty didn't believe in Truth with a capital T."),
        ("colour", "Thought the mind doesn't 'mirror' reality -- there's no God's-eye view to check our answers against. Just better and worse ways of coping, of describing things for what we want."),
        ("pbp", "Sounds slippery."),
        ("colour", "He'd call it honest. Don't ask if a racing line is 'truly' correct -- ask if it gets you to the flag quicker. Works? Keep it. That's his whole philosophy and most of good engineering."),
    ], about=("Richard Rorty",), topic="no mirror of nature"),

    discussion([
        ("pbp", "Diogenes -- citizen of where, exactly?"),
        ("colour", "Asked where he was from, he said 'I am a citizen of the world.' First man on record to say it. No city, no flag, no allegiance he hadn't chosen himself."),
        ("pbp", "No team orders, then."),
        ("colour", "None he'd honour. The pit wall can call till it's hoarse. He recognises no authority but his own nose, and possibly the barrel."),
    ], about=("Diogenes",), topic="cosmopolitan"),

    discussion([
        ("pbp", "Rand's philosophy in a sentence, Benny?"),
        ("colour", "'A is A.' Reality is what it is, reason's your only tool, and your own happiness is the point. She called selfishness a virtue and meant it as the highest praise."),
        ("pbp", "Not a team player."),
        ("colour", "She'd say 'team' is how the weak guilt the able. Bold line from a car that retires every week. Reality is what it is, Ayn -- and the wall's been A-is-A-ing you all season."),
    ], about=("Ayn Rand",), topic="a is a"),

    discussion([
        ("pbp", "Stirner and his 'spooks.' What's a spook?"),
        ("colour", "Any grand abstraction you let boss you about. The State. Morality. Humanity. God. He says they're ghosts -- real only because you bow. Stop bowing and they vanish."),
        ("pbp", "Including the rulebook."),
        ("colour", "Especially the rulebook. He'd treat a blue flag as a haunting. Which is precisely why he and Rand are sat in the gravel debating property rights with a marshal."),
    ], about=("Max Stirner",), topic="spooks"),

    discussion([
        ("pbp", "Emma Goldman -- 'if I can't dance...'"),
        ("colour", "'...it's not my revolution.' Probably never said it word for word, but it's pure her: no liberation worth having grinds the joy out of you. Freedom should FEEL like something."),
        ("pbp", "And out there?"),
        ("colour", "She races like she means it. Anarchism with a sense of fun -- which the dour lads on the Vanguard pit wall never could stand. Marx wanted the committee. Emma wanted the music."),
    ], about=("Emma Goldman",), topic="dancing"),

    discussion([
        ("pbp", "Bakunin -- the destruction line we know. Did he ever build anything?"),
        ("colour", "He'd say destruction IS the building. Tear out the rotten structure and something freer grows in the gap. Not nihilism -- gardening, with dynamite."),
        ("pbp", "Into Turn 1--"),
        ("colour", "--he's pruning. Aggressively. Marx wanted a plan and a party; Bakunin wanted everyone free NOW and the wreckage tidied later. You can hear which one's quicker off the line."),
    ], about=("Mikhail Bakunin",), topic="creative destruction"),

    discussion([
        ("pbp", "Wollstonecraft -- 'A Vindication of the Rights of Woman.'"),
        ("colour", "The first great feminist text, 1792. Deceptively simple argument: women seem lesser only because they're schooled to be. Give them reason and a real education and watch."),
        ("pbp", "Ahead of her time."),
        ("colour", "By centuries. Pub fact for you -- her daughter wrote Frankenstein. Whole family specialised in building what nobody was ready for. Tidy driver, too. Not a wasted input."),
    ], about=("Mary Wollstonecraft",), topic="vindication"),

    discussion([
        ("pbp", "Cesaire's 'Discourse on Colonialism' -- the central idea?"),
        ("colour", "The boomerang. He argued the brutality Europe practised abroad came home -- the violence it exported eventually flew back and savaged Europe itself."),
        ("pbp", "Heavy stuff."),
        ("colour", "It is. And he wrote it like poetry, because he WAS a poet. Measured, composed, every word placed. Drives the same way -- nothing flashy, nothing wasted, and it all lands."),
    ], about=("Aimé Césaire",), topic="boomerang"),

    discussion([
        ("pbp", "Fanon was a doctor, wasn't he?"),
        ("colour", "Psychiatrist. Treated the colonised AND the colonisers in Algeria, and found the same sickness warping both. 'Black Skin, White Masks' -- what it does to a mind to be taught it's lesser."),
        ("pbp", "So decisive out there."),
        ("colour", "Because he believed thinking had to BECOME doing or it was worthless. A diagnosis you never act on is just a tidy way of giving up. He never gave up on a thing. It's in every move."),
    ], about=("Frantz Fanon",), topic="psychiatrist"),

    discussion([
        ("pbp", "Thomas Paine -- 'These are the times that try men's souls.'"),
        ("colour", "Wrote that in a freezing army retreat, by firelight, to keep a beaten rabble in the fight. And it worked. The man could turn a sentence into a recruiting sergeant."),
        ("pbp", "Plain speaker."),
        ("colour", "All of it for the ordinary reader, none for the salon. And he designed iron bridges on the side -- proper engineer's brain. No nonsense in the prose, none in the racing."),
    ], about=("Thomas Paine",), topic="times that try"),

    discussion([
        ("pbp", "Marcuse -- 'One-Dimensional Man.'"),
        ("colour", "His fear was a society so comfortable it can't imagine an alternative. Enough gadgets and a choice between brands, and people stop dreaming of anything genuinely different."),
        ("pbp", "And the Great Refusal?"),
        ("colour", "The way out: refuse the whole rigged menu. Don't pick the options -- reject the question. Trouble is, out here the only refusal that scores is refusing to lift. He's quite good at that."),
    ], about=("Herbert Marcuse",), topic="one-dimensional"),

    discussion([
        ("pbp", "Derrida -- 'there is no outside-text.' Meaning?"),
        ("colour", "Everything you grab to pin a meaning down turns out to be more words needing more words. No solid floor under any of it. Meaning keeps slipping, deferring, away."),
        ("pbp", "So a result--"),
        ("colour", "--he'd say even the timing sheet's a text you have to interpret. Funny thing is, the marshals find his car perfectly easy to read. It's the one in the wall."),
    ], about=("Jacques Derrida",), topic="outside-text"),

    discussion([
        ("pbp", "Adorno's a hard man to please."),
        ("colour", "Impossible. Said that after the century's horrors, even art was compromised. And he HATED jazz -- thought it fake rebellion, mass-produced spontaneity. Imagine telling him about podium music."),
        ("pbp", "He'd despair."),
        ("colour", "He'd write four hundred pages on the champagne spray as commodified joy. Never happy -- and that's exactly why he spots the cracks the rest of us walk straight past."),
    ], about=("Theodor Adorno",), topic="no poetry"),

    discussion([
        ("pbp", "A Luxemburg line everyone quotes?"),
        ("colour", "'Freedom is always the freedom of the one who thinks differently.' And she aimed it at her OWN side -- told the revolution that the moment it silenced its critics, it had already lost."),
        ("pbp", "Brave."),
        ("colour", "Fearless. Argued it with Lenin to his face. Trusted the masses to find their own way -- spontaneity over the iron committee. Drives exactly like that. Trusts the moment, and she's usually right."),
    ], about=("Rosa Luxemburg",), topic="freedom to differ"),

    # --- more rivalries: the cross-team grudges that make a grid --------------
    discussion([
        ("pbp", "Nietzsche and Marx, side by side -- the two heavyweights."),
        ("colour", "Total opposites. Marx says history's driven by impersonal forces -- economics, class, the system. Nietzsche says nonsense, it's driven by the will of exceptional individuals."),
        ("pbp", "Forces versus the great man."),
        ("colour", "There it is in miniature. Marx back there nursing the tyres, trusting the long material grind. Nietzsche flinging it up the inside, trusting only himself. The whole argument, live."),
    ], about=("Friedrich Nietzsche", "Karl Marx"), topic="forces vs will"),

    discussion([
        ("pbp", "Two political minds here -- Plato and Machiavelli."),
        ("colour", "And they could not disagree more. Plato wants the wisest, most virtuous soul to rule -- the philosopher-king. Machiavelli says spare me, study how power ACTUALLY works."),
        ("pbp", "Ideal versus real."),
        ("colour", "Plato races the perfect lap in his head. Machiavelli races the one that wins on Sunday. And history, I'm afraid, is rather unkind to the dreamers."),
    ], about=("Plato", "Niccolò Machiavelli"), topic="ideal vs real"),

    discussion([
        ("pbp", "Rorty spent a career arguing with Plato -- across the centuries."),
        ("colour", "Demolishing him, in his own words. Plato started the idea there's one true reality behind appearances and philosophy's job is to find it. Rorty called the whole two-thousand-year project a wrong turn."),
        ("pbp", "Cheeky."),
        ("colour", "He just wanted us to stop asking 'is it TRUE' and start asking 'is it USEFUL.' Plato would be horrified. Which, watching them race the same tarmac, is rather the joy of it."),
    ], about=("Richard Rorty", "Plato"), topic="rorty vs plato"),

    discussion([
        ("pbp", "Foucault and Marx -- both about power, surely allies?"),
        ("colour", "You'd think. But Marx puts power in who owns the factory -- class and money. Foucault said no, power's everywhere, in every relationship: doctor and patient, teacher and pupil."),
        ("pbp", "Diffuse versus concentrated."),
        ("colour", "Marx wants to seize the means of production. Foucault would ask who decided 'production' was the thing worth seizing. Drove the Marxists up the wall, which he rather enjoyed."),
    ], about=("Michel Foucault", "Karl Marx"), topic="power diffuse"),

    discussion([
        ("pbp", "Goldman and Marx -- both on the left, miles apart."),
        ("colour", "A chasm. Marx says seize the state and build socialism with it. Goldman the anarchist says the STATE is the disease -- you don't cure tyranny by grabbing the whip yourself."),
        ("pbp", "No bosses, even red ones."),
        ("colour", "Especially red ones. She watched a revolution build a shinier cage and walked away disgusted. Marx wants the committee to plan the race. Emma wants no committee at all."),
    ], about=("Emma Goldman", "Karl Marx"), topic="state vs none"),

    discussion([
        ("pbp", "Here's a contrast -- Diogenes and Rand on the same lap."),
        ("colour", "The funniest pairing out there. Diogenes owned a barrel and a cup, until he saw a child drink from its hands and chucked the cup. Rand built a cathedral to property and achievement."),
        ("pbp", "The man with nothing and the apostle of having."),
        ("colour", "One thinks the secret to wealth is wanting nothing; the other thinks it's earning everything. And the kicker -- the man with the barrel finishes more races than the woman with the principles."),
    ], about=("Diogenes", "Ayn Rand"), topic="having and not"),

    discussion([
        ("pbp", "de Beauvoir and Nietzsche -- both about making yourself."),
        ("colour", "Close cousins. Both say there's no fixed essence handed down -- you forge who you are by what you do. But his is a lone hero's project; hers is done in a world full of other people."),
        ("pbp", "Freedom with company."),
        ("colour", "Her sharpest jab at him: your freedom's bound up with everyone else's. The lone superman's a fantasy -- nobody authors a self in a vacuum. More grown-up, frankly. And every bit as quick."),
    ], about=("Simone de Beauvoir", "Friedrich Nietzsche"), topic="self-creation"),

    discussion([
        ("pbp", "Paine and Marx -- two revolutionaries, two different revolutions."),
        ("colour", "Paine's is about RIGHTS -- liberty, a fair vote, the dignity of the common man. Very hopeful, very eighteenth century. Marx came along and asked, lovely, but who owns the printing press?"),
        ("pbp", "Political versus economic."),
        ("colour", "Paine frees you to vote; Marx asks what the vote's worth if you're starving. Both right about something. Both, out here, a good deal slower than the man who only wants to win."),
    ], about=("Thomas Paine", "Karl Marx"), topic="two revolutions"),

    # --- thematic threads: the philosophy OF racing, not just the racers -----
    discussion([
        ("pbp", "Three anarchists on this grid. How do they cope with a rulebook?"),
        ("colour", "Badly. Gloriously. Bakunin wants to smash it, Goldman to dance round it, Stirner reckons it's a ghost. Not one accepts a steward has the right to tell them anything at all."),
        ("pbp", "And yet they signed on."),
        ("colour", "That's the lovely contradiction. You can't race without agreeing to SOME rules, even just to break them. Every anarchist's secret problem, right there on the entry list."),
    ], topic="the rulebook"),

    discussion([
        ("pbp", "Big one, Benny: is the result decided before lights-out?"),
        ("colour", "Depends who you ask. Marx would say the material conditions all but settle it. The existentialists would be appalled -- every corner's a free choice, nothing's written."),
        ("pbp", "And you?"),
        ("colour", "Forty years in this game, I've seen the fastest car lose and the certain winner crash on the formation lap. I lean existentialist by about teatime on a Sunday."),
    ], topic="free will"),

    discussion([
        ("pbp", "How much of this is luck, do you reckon?"),
        ("colour", "Machiavelli had the figure -- about half. Half fortuna, half what you make of it. The rain, the safety car, the lap your rival hits traffic. That's the river flooding."),
        ("pbp", "And the other half?"),
        ("colour", "Being ready when it does. The prepared driver calls it skill, the unlucky one calls it fate, and they're describing the same wet Tuesday. Luck favours the one who packed the inters."),
    ], topic="luck"),

    discussion([
        ("pbp", "The Objectivism garage. Optimistic this week?"),
        ("colour", "Never been optimistic in my life and I'm not starting for Rand and Stirner. The one philosophy on the grid that refuses, on principle, to be told when to pit."),
        ("pbp", "And so--"),
        ("colour", "--and so they don't finish. Ever. Two brilliant minds who'd each sooner expire in the gravel than admit the team might know a thing. There's a lesson there. They will not be learning it."),
    ], topic="objectivists"),

    discussion([
        ("pbp", "What would this lot make of winning, as an idea?"),
        ("colour", "Oh, they'd never agree. Nietzsche LOVES it -- overcoming, the whole point of being alive. Marx is suspicious -- competition's just the system setting workers at each other's throats."),
        ("pbp", "And the rest?"),
        ("colour", "Rand thinks the winner earned every inch and owes nobody. Goldman thinks the trophy's a leash. Diogenes wouldn't cross the room for it. Twenty reasons to be here, one flag to settle it."),
    ], topic="winning"),

    discussion([
        ("pbp", "Spare a thought for the midfield, Benny."),
        ("colour", "Always do. Half of philosophy IS the midfield -- the ones history half-remembers, grinding away, occasionally brilliant, mostly overlooked. Rorty had a lovely humility about that."),
        ("pbp", "No shame in finishing tenth?"),
        ("colour", "None. A useful idea that finishes tenth beats a perfect one in the gravel. Most of these geniuses died ignored and got famous later. Bit late for the points, mind you."),
    ], topic="the midfield"),

    # --- driver at a particular circuit --------------------------------------
    discussion([
        ("pbp", "Bakunin at Monza -- the destroyer at the Temple of Speed."),
        ("colour", "Worst possible combination, best possible viewing. Longest straights on the calendar and a man whose entire creed is 'send it and sort the wreckage later.' He'll either lead or barrel-roll."),
        ("pbp", "No in-between."),
        ("colour", "Never is with Bakunin. The slipstream just gives the urge to destroy more runway. Wonderful while it lasts -- and you can set your watch by the gravel trap."),
    ], about=("Mikhail Bakunin",), track="Monza", topic="bakunin at monza"),

    discussion([
        ("pbp", "Machiavelli at Monaco -- the strategist's fortress."),
        ("colour", "His ideal afternoon. Can't pass round here for love nor money, so the whole thing's settled on cunning -- track position, the undercut, the perfectly judged stop. No brute force, all brain."),
        ("pbp", "Made for him."),
        ("colour", "Tailor-made. Monaco's a chessboard with barriers, and he's the only one who brought a chessboard. Everyone else is hoping. He's planning. Round here, that's the win."),
    ], about=("Niccolò Machiavelli",), track="Monte Carlo", topic="machiavelli at monaco"),

    discussion([
        ("pbp", "de Beauvoir at Suzuka -- precision meets the most precise track there is."),
        ("colour", "A match made in heaven. Suzuka punishes the smallest sloppiness; that figure-of-eight demands you commit early and mean it. Her whole philosophy is rigorous, deliberate self-authorship."),
        ("pbp", "No room for waffle."),
        ("colour", "None through the Esses, none in her prose. Every input placed exactly, nothing for show. If a circuit could read a book, Suzuka would read hers and nod."),
    ], about=("Simone de Beauvoir",), track="Suzuka", topic="beauvoir at suzuka"),

    discussion([
        ("pbp", "Marx at Interlagos, Benny."),
        ("colour", "He'd love this place. Built in a working district, the people's circuit, the crowd practically leaning into the cars. Senna country -- a hero who came from where the fans actually live."),
        ("pbp", "Material conditions and all that."),
        ("colour", "Right up his street. Short lap, relentless, decided by grind and grip and who manages the heat. He races the long game like a religion -- this track might just reward the sermon."),
    ], about=("Karl Marx",), track="Interlagos", topic="marx at interlagos"),

    discussion([
        ("pbp", "Rand at Spa, and there's weather about."),
        ("colour", "Oh, this is delicious. Her whole creed is that reality bends to the rational individual. Spa's microclimate bends to NOBODY -- raining at Eau Rouge, dry at the Bus Stop, same lap."),
        ("pbp", "Reality won't co-operate."),
        ("colour", "Reality is what it is, she says. And Spa says: yes, and what I AM is unpredictable, so pack the inters like everyone else. She won't. She never does. Hello, gravel."),
    ], about=("Ayn Rand",), track="Spa-Francorchamps", topic="rand at spa"),
]


# =============================================================================
# THE SHOWS -- material the pre/post-race segments draw on.
# =============================================================================

# A quick scene-setting beat for the pre-race show (the deeper track talk lives in
# DISCUSSIONS, saved for the race itself).
TRACK_LORE = {
    "Monza": [banter([("pbp", "Monza. The Temple of Speed."),
                     ("colour", "Big tow, late on the brakes, tifosi screaming for red. Can't not love it.")], when="any")],
    "Monte Carlo": [banter([("pbp", "Monte Carlo -- the jewel in the crown."),
                           ("colour", "And a fortress. Nowhere to pass, one mistake and your Sunday's done. Track position is everything.")], when="any")],
    "Spa-Francorchamps": [banter([("pbp", "Spa-Francorchamps. Through the Ardennes."),
                                 ("colour", "Eau Rouge, its own weather, the lot. The drivers' favourite, every one of them.")], when="any")],
    "Silverstone": [banter([("pbp", "Silverstone -- where it all began, 1950."),
                           ("colour", "Maggotts and Becketts'll tell you who's brave and who just talks about it.")], when="any")],
    "Suzuka": [banter([("pbp", "Suzuka. The only figure-of-eight on the calendar."),
                      ("colour", "Crosses over itself, forgives nothing. Hallowed ground.")], when="any")],
    "Interlagos": [banter([("pbp", "Interlagos. Short, anticlockwise, deafening."),
                          ("colour", "Senna's home crowd. Where championships come to be decided.")], when="any")],
}


# Post-race podium quotes -- the DRIVERS speak, each in their own voice.
PODIUM_QUOTES = {
    "Plato": ["The perfect race exists in a higher realm. Today I drove its shadow -- and the shadow was enough.",
              "The wise should rule, and the wise should win. I see no contradiction in today's result."],
    "Diogenes": ["I now own a barrel and a trophy. I shall be keeping the barrel.",
                 "I asked for nothing and won everything. Recommend it to the others."],
    "Karl Marx": ["The history of all racing is the history of strategy. Today, the strategy was correct.",
                  "The pit wall has nothing to lose but its chains -- and today, a race to gain."],
    "Rosa Luxemburg": ["I followed no master plan. The moment told me when to strike, and I listened.",
                       "Freedom is the freedom to take the line nobody sanctioned. I took it."],
    "Mikhail Bakunin": ["I dismantled the field. The urge to destroy, as I have always said, is a creative one.",
                        "They built a grid. I unbuilt it, from the front backwards."],
    "Emma Goldman": ["If I cannot dance on the podium, I do not want it. ...I will, however, take the trophy.",
                     "No gods, no masters, no team orders. Just me and a very good afternoon."],
    "Friedrich Nietzsche": ["That which does not overtake me makes me stronger. I overtook all of them.",
                            "I did not find the limit. I became it, and then I went past."],
    "Simone de Beauvoir": ["One is not born a winner. One becomes one -- braking point by braking point.",
                           "I authored every metre of that. Nothing today was given to me."],
    "Niccolò Machiavelli": ["It is better to be feared on the pit wall than loved. They feared my strategy, and rightly.",
                            "Fortune favoured me, yes. But I had built the banks before her river rose."],
    "Richard Rorty": ["There is no deep truth about who deserved this. There is only the timing screen, and I am atop it.",
                      "Was it the 'right' way to win? Wrong question. It worked. That is the only test."],
    "Theodor Adorno": ["A victory under these conditions merely flatters the spectacle. ...It was, nonetheless, delightful.",
                       "I shall enjoy this for precisely as long as it takes me to find it suspect."],
    "Herbert Marcuse": ["I refused to lift. The Great Refusal -- performed at two hundred miles an hour.",
                        "They offered me the sensible line. I declined the whole menu."],
    "Michel Foucault": ["Every driver out there was disciplined by the circuit. I disciplined the circuit.",
                        "They were all being watched. I was the one who decided where to look."],
    "Jacques Derrida": ["There is no outside-the-podium. There is also, strictly, no podium. I won it regardless.",
                        "The result resists final interpretation. The trophy, happily, does not."],
    "Frantz Fanon": ["They built this sport to keep us out. Today the grid belonged to the excluded.",
                     "I did not wait for permission to win. One never is given it."],
    "Aimé Césaire": ["I gave a generation its words. Today I gave them the fastest lap as well.",
                     "Measured, composed, and first. The poem and the result, for once, agreed."],
    "Thomas Paine": ["These are the laps that try drivers' souls. Plain courage won out, as it tends to.",
                     "No cunning, no theatre. Common sense, applied at speed, and a fair result."],
    "Mary Wollstonecraft": ["Let the record show: reason, not force, took this victory.",
                            "Educate a driver properly and this is what you get. I rest the case."],
}

PODIUM_QUOTE_FALLBACK = [
    "A good day's work. The arguments can wait until tomorrow.",
    "I will let the result speak. It is more eloquent than I am.",
]


# =============================================================================
# THE PODIUM INTERVIEW -- a real give-and-take, not a recited quote. A pit-lane
# reporter (role "report") asks questions DRAWN FROM THE RACE THAT JUST HAPPENED
# -- the charge through the field, the scrap with a teammate, the call on the
# tyres -- and the driver answers. Racing first; the philosophy is the CLOSER,
# the existing PODIUM_QUOTES line that buttons the interview. (The colour.py
# fact-finder decides which angles actually apply to each finisher.)
#
# Question banks are keyed by ANGLE. Placeholders the booth fills: {mate} (the
# teammate's name), {gained} (spelled cardinal), {start_ord} (spelled ordinal).
# =============================================================================

# The booth throws down to the podium.
PODIUM_HANDOFF = [
    ("pbp", "Let's get down to the podium -- Suze is standing by."),
    ("pbp", "Our Suze is down with the drivers. Suze?"),
    ("pbp", "Over to pit lane, where Suze has the podium finishers."),
]

PODIUM_QUESTIONS = {
    "charge": [
        "{gained} places up from where you started -- talk us through that charge.",
        "You came right through the field today -- where did you make the difference?",
        "From {start_ord} on the grid to the podium -- how did that one come together?",
    ],
    "teammate": [
        "You and {mate} had quite the battle out there -- how close did that get?",
        "It looked like you and {mate} were really racing each other hard today?",
        "That scrap with {mate} -- was it as tense in the car as it looked from here?",
    ],
    "team_orders": [
        "Were team orders ever a consideration, or were you both free to race?",
        "Did the pit wall ever ask you to hold position, or was it gloves off?",
        "Was there ever a call to settle it between you, or were you let race?",
    ],
    "weather": [
        "When the rain came, what was the call on the tyres?",
        "The conditions were all over the place -- how did you read them?",
        "That gamble when the weather turned -- talk us through the thinking.",
    ],
    "survival": [
        "You took a knock out there and still brought it home -- how was the car after?",
        "There was contact early on -- how close did you come to not finishing?",
        "You carried damage to the flag -- how much was that hurting you out there?",
    ],
    "pole_to_win": [
        "Pole to flag, never headed -- was it as controlled as it looked from here?",
        "You led every lap -- was it ever as comfortable as the gap suggested?",
        "Lights to flag out front -- where was this race actually won?",
    ],
    "win_open": [
        "Take us through it -- when did you know the win was on?",
        "A brilliant drive -- where do you reckon you won this one?",
        "When did you start to believe today was your day?",
    ],
}

# The closing question -- the cue for the driver's philosophy line (PODIUM_QUOTES).
PODIUM_CLOSER_Q = {
    "winner": [
        "And the bigger picture -- what does a win like this mean to you?",
        "Finally, sum it up for us. What does this one mean?",
        "Last word's yours -- what does a day like this say?",
    ],
    "other": [
        "And the bigger picture -- happy to be up there?",
        "Last word -- what do you take away from today?",
        "Sum it up for us -- satisfied with that result?",
    ],
}

# The GENERIC answer floor -- in a neutral racing register, fits any driver's
# mouth. The booth uses these unless the driver has a characterful override below.
PODIUM_ANSWER_GENERIC = {
    "charge": [
        "We were quick where it mattered and patient where we had to be. The places came.",
        "I kept my head, picked them off one at a time, and trusted the car would still be there at the end. It was.",
        "Once you're past the first two it becomes a rhythm. You stop counting and just keep moving forward.",
    ],
    "teammate": [
        "Hard but fair. We've earned the right to race each other, and we did -- cleanly.",
        "Close. Closer than the team would have liked, I should think. But that's racing.",
        "We pushed each other all afternoon. That's what a good pairing is for -- nobody got a free ride.",
    ],
    "team_orders": [
        "We were free to race. It's the only way I'd want it.",
        "No orders. We sorted it on the track, the way it should be.",
        "If there was a call to hold station, I'd like to think I heard it... eventually.",
    ],
    "weather": [
        "You commit to a read and you live with it. Today the read was right.",
        "Half of it is nerve. You can't wait to be certain -- by then you've lost it. I went early, it paid.",
        "The track tells you, if you're listening. I listened a fraction sooner than the rest.",
    ],
    "survival": [
        "She was bruised, but she answered. You drive around the damage and hope it holds. It held.",
        "Wounded but willing. You shorten the braking, you nurse it, you count the laps down.",
        "Not pretty after that knock. But a damaged car on the podium beats a perfect one in the gravel.",
    ],
    "pole_to_win": [
        "Never as easy as it looks. You're managing the gap, the tyres, your own mind, every lap.",
        "Controlled, yes -- but control is work. The moment you relax out front is the moment it slips.",
        "From the front you race the track and your own concentration. Both tried to catch me out.",
    ],
    "win_open": [
        "When the gap behind me stopped coming down, I let myself believe it. Not before.",
        "There's a moment the car comes to you and everything else goes quiet. After that, just laps.",
        "I knew when I crossed the line, and not a corner sooner. You never count it before then.",
    ],
}

# CHARACTER OVERRIDES -- the authored gold, keyed by driver then angle. Where a
# driver has a line for the angle being asked, it's used instead of the generic
# floor; everything else falls through gracefully. This is where the philosophy
# earns its place -- by answering a RACING question in the driver's own voice.
PODIUM_ANSWERS = {
    "Emma Goldman": {
        "teammate": ["Bakunin and I would be ashamed to hold station for one another. We raced flat out -- it's the only honest way."],
        "team_orders": ["Orders? On THIS team? They wouldn't dare key the radio. We settle it on the track, every single time."],
    },
    "Mikhail Bakunin": {
        "teammate": ["Hold station for Goldman? She'd never forgive me, and I'd never forgive myself. We tear it down together, the pair of us."],
        "win_open": ["I attacked from lights to flag and never once thought about managing it. Lead, lose it, take it straight back -- that is my whole race plan.",
                     "I have one gear: forward, hard. It went wrong for everyone but me today, which is roughly the plan."],
    },
    "Frantz Fanon": {
        "teammate": ["Closer than the timing screen will ever show. He taught me everything I know about racing. He did not, today, teach me to lift."],
        "team_orders": ["Hold position behind my old teacher? No. I respect him far too much to insult him by lifting."],
        "charge": ["I saw the gaps and I took them. You do not wait to be granted a place out here -- you go and you take it."],
    },
    "Aimé Césaire": {
        "teammate": ["Fanon races like the student who outgrew the lesson. I taught him patience; he has clearly mislaid it. No matter -- it was a fine fight."],
        "pole_to_win": ["I let the hotheads tear past and tear themselves up. Clean lines, cool head -- and there was the win, waiting at the end."],
        "win_open": ["Composed all the way down. I wrote the lap out longhand and it proved quicker than their shouting."],
    },
    "Niccolò Machiavelli": {
        "weather": ["The plan accounted for the rain before the first cloud arrived. Fortune merely confirmed what preparation had already decided."],
        "win_open": ["I knew at lights-out. The result was settled on the pit wall on Thursday; today was merely its execution."],
        "charge": ["Cunning, not force. I let them tire themselves fighting, and arrived, unhurried, at the front."],
    },
    "Karl Marx": {
        "charge": ["It was not heroics. It was the conditions, read correctly and applied patiently, lap after lap. The order corrects itself in the end."],
        "win_open": ["History was on my side this afternoon. So were the tyres. Today, the two were the same thing."],
        "weather": ["The material conditions shifted, and I adapted to them before the others noticed they had. That is the whole of strategy."],
    },
    "Friedrich Nietzsche": {
        "charge": ["I held position exactly never. Forward was the only direction I was willing to recognise, so forward I went."],
        "survival": ["The knock sharpened me. I drove harder after it than most manage with an unmarked car."],
        "win_open": ["I took the lead, and then I simply kept taking. At no corner did I decide I had enough.",
                     "I drove every lap as though I would have to drive it again forever. That tends to be quick."],
    },
    "Simone de Beauvoir": {
        "charge": ["Nothing out there was given to me. I made every place, one decision at a time, and lived with each one."],
        "pole_to_win": ["One is not born in front -- one stays there by choosing well, corner after corner. I chose well."],
    },
    "Michel Foucault": {
        "weather": ["I'd committed to my move while the rest were still waiting for the wall to commit for them. That one lap was the race."],
        "win_open": ["The track herds everyone onto the same line. I spent the afternoon taking the ones it didn't want me to take."],
    },
    "Rosa Luxemburg": {
        "weather": ["I didn't wait to be told. I saw the track turning and came in a lap before the pit wall would have called it."],
        "win_open": ["From fourth, I picked my laps and pounced when the gaps came. You can't plan that -- you feel it, and you go."],
    },
    "Plato": {
        "pole_to_win": ["I drove the lap I had already seen, complete, in my mind. The rest were chasing a shadow of it."],
        "win_open": ["I had driven the whole race in my head before lights-out. Out there I simply matched the picture, corner by corner.",
                     "No surprises. I had seen this race complete before the lights went out, and I spent the afternoon making the world agree with it."],
    },
    "Diogenes": {
        "win_open": ["I expected nothing and arrived first. I recommend the method to the others."],
        "team_orders": ["Team orders? I recognise no authority but my own. The pit wall is welcome to shout into its barrel."],
    },
    "Jacques Derrida": {
        "win_open": ["I found the gap where their certainty about the line used to be, and was through it before they noticed it had gone."],
        "charge": ["I unpicked their certainty about the racing line until there was a gap where their confidence had been. Then I drove through it."],
    },
    "Mary Wollstonecraft": {
        "charge": ["I took the chances I was owed and made each one count. No heroics -- just moving forward, place by place, all afternoon."],
        "win_open": ["Clear thinking, lap after lap. I didn't out-muscle anyone today -- I out-reasoned them into the braking zones."],
    },
    "Thomas Paine": {
        "win_open": ["No cunning, no theatre. Plain courage, plainly applied. It tends to be enough."],
        "survival": ["She was bent, not broken. I shortened the braking, nursed the damage, and counted every last lap down to the flag."],
    },
    "Herbert Marcuse": {
        "charge": ["Every corner the others backed out of, I stayed in. That is where each of those places came from -- the moment they lifted and I did not."],
        "survival": ["The sensible move was to back out. I declined the sensible move, as is my habit."],
    },
    "Theodor Adorno": {
        "win_open": ["I drove a controlled, joyless, maximally efficient race. I'm told that is not how one is meant to enjoy it. I enjoyed it regardless."],
        "pole_to_win": ["From the front it is all management -- the gap, the tyres, one's own creeping suspicion of the whole enterprise. I managed all three."],
    },
    "Richard Rorty": {
        "weather": ["I went to the inters a lap before the textbook said to. Did it look right? No idea -- it put me up the road, which is all I asked of it."],
        "win_open": ["I stopped wondering whether my line was 'truly' the quickest and just drove the one that kept working. It kept working all day."],
    },
}
