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

ON VOICE (the full character bible lives in colour.py, by PERSONAS): Phill (pbp) is
no mook -- he knows the theory and the history, but his job is the LISTENER, so he
draws Benny out on both the philosophy and the racecraft. Both men are steeped in
Monty Python, the Simpsons, and Douglas Adams, and it leaks out despite their best
professional efforts: deadpan absurdism, the bleak-but-cheerful aside, over-precise
pedantry, the non-sequitur left unacknowledged -- then a brisk snap back to the
racing. Write the funny line straight-faced; write every line to those two voices.

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
    # The teaching layer: each line carries the thinker's politics through the
    # racing -- the move first, the idea riding on top. Tags that actually fire
    # (see colour.for_overtake/for_incident/for_pit): "start", "overtake",
    # "incident", "retirement", "pit". A flat colour line gets the duo texture
    # (a Benny opener, sometimes a Phill reclaim); banters pass through as written.
    "Plato": [
        quip("Plato away cleanly -- the philosopher-king takes the place that's his by right, he'd say.", when="start"),
        quip("Plato through, and precisely where he meant to be -- the perfect line isn't out here on the tarmac, he reckons, it's the one he's already driven in his head. He's only matching the picture.", when="overtake"),
        quip("Even the architect of the perfect society can't legislate away a kerb.", when="incident"),
        quip("Off chasing the ideal line -- and the bother with ideal lines, like ideal cities, is they live up in the head and not down here in the gravel.", when="incident"),
        quip("A stop timed to the second -- Plato wants the whole race run like his Republic, every part in its ordained place, the pit wall included.", when="pit"),
    ],
    "Diogenes": [
        quip("Diogenes away like a man with nothing to lose -- which, owning a barrel, he hasn't.", when="start"),
        quip("Diogenes barges through on pure instinct -- no tow, no plan, no thank-you. All the clever strategy's just borrowed nonsense, he reckons; strip it off and you've a man and a corner, and he prefers it that way.", when="overtake"),
        quip("No plan, no shame, no brakes. Living the dream, right up until the gravel.", when="incident"),
        quip("There it goes. The Cynic never did believe in the rules, including the ones holding the car on the road.", when="incident"),
    ],
    "Karl Marx": [
        quip("Marx away patiently -- he's not interested in the launch, he's interested in lap forty. The whole race is a process, and he's already read how it ends.", when="start"),
        quip("Marx grinds past at last -- no lunge, no luck, just the long game arriving bang on schedule. The order corrects itself, he'd say, given enough laps.", when="overtake"),
        quip("Even the man who mapped the whole arc of history can lose the back end at the Roggia. The material conditions, just then, included a damp kerb.", when="incident"),
        quip("A calculated stop -- the man does nothing without a theory of why.", when="pit"),
    ],
    "Rosa Luxemburg": [
        quip("Luxemburg sends it -- didn't wait for the order, never does.", when="start"),
        quip("Luxemburg pounces -- no call from the pit wall, no committee, just the gap and the nerve to take it. She always did trust the moment over the master plan.", when="overtake"),
        quip("Caught out chasing a half-gap there -- she races on instinct, and instinct, now and again, drives you into the scenery. She'd still take it over waiting to be told.", when="incident"),
    ],
    "Mikhail Bakunin": [
        quip("Bakunin attacks Turn 1 like it owes him money. The urge to destroy, he calls it.", when="start"),
        quip("Bakunin barges through -- no master, no plan, no permission asked. He'd tear up the pit wall's strategy if they ever dared send him one.", when="overtake"),
        quip("Urge to destroy's a creative one, he says. Very creative with the barrier just then.", when="incident"),
        quip("Down it goes. He always did prefer tearing things down to keeping them up.", when="incident"),
    ],
    "Emma Goldman": [
        quip("Goldman dances off the line -- if she can't enjoy the start, it's not her revolution.", when="start"),
        quip("Goldman dances past, and loving every yard of it -- a revolution you can't enjoy isn't worth having, she'd say. Same, it turns out, goes for an overtake.", when="overtake"),
        quip("Off she goes, having far too much fun -- but she'd sooner bin it chasing the joy than tiptoe round for points. That's the whole creed, right there in the gravel.", when="incident"),
        quip("In she comes -- under protest, you suspect. Goldman trusts an order about as far as she could throw the pit wall that gave it.", when="pit"),
    ],
    "Friedrich Nietzsche": [
        quip("Nietzsche living dangerously into Turn 1, as advertised.", when="start"),
        quip("Nietzsche forces his way through -- forward's the only direction he'll recognise. Will to power, and just now it's the will to a better corner exit.", when="overtake"),
        quip("Will to power, that. The will to understeer, more like.", when="incident"),
        quip("He gazed into the abyss once too often -- and this time it gazed back.", when="incident"),
        quip("Nietzsche boxes, and you can hear him hating it -- sat still, trusting the herd in the pit lane. Everything in the man wants to be back out there overcoming something.", when="pit"),
    ],
    "Simone de Beauvoir": [
        quip("de Beauvoir away, and nothing about it left to chance -- she chooses this start the way she chooses everything, deliberately, and lives with it.", when="start"),
        quip("de Beauvoir makes the place -- doesn't wait to be granted it. One is not born in front, she'd say; one gets there by choosing well, corner after corner.", when="overtake"),
        quip("Even the most rigorous plan has to meet the situation -- and the situation, just there, was a kerb she didn't choose. She'll account for it precisely afterwards.", when="incident"),
        quip("A stop worked out to the letter -- de Beauvoir leaves nothing to fortune that she can settle by thinking it through first.", when="pit"),
    ],
    "Niccolò Machiavelli": [
        quip("Machiavelli holds his line off the start -- no heroics. He decided where this race was won on Thursday, and it wasn't at Turn 1.", when="start"),
        quip("Machiavelli through, and never laid a wheel in anger -- let the others wear themselves out fighting; he simply arrived, unhurried, and took the place. Cunning beats force.", when="overtake"),
        quip("Machiavelli boxes -- exactly when it suits him and nobody else. The ends justify the in-lap.", when="pit"),
    ],
    "Richard Rorty": [
        quip("Rorty away tidily -- no grand theory of the perfect start, just whatever gets the job done off this particular line on this particular day.", when="start"),
        quip("Rorty finds a way by -- he never stopped to wonder whether his line was 'truly' the quickest, he just kept driving the one that was working. And it kept working.", when="overtake"),
        quip("Caught out there -- and there's no deeper truth to fall back on, in his book, just the next corner to get right. He'll shrug and get on with it.", when="incident"),
        quip("A sensible, unfussy stop -- Rorty asks one question of a strategy and one only: does it put me up the road? This one did.", when="pit"),
    ],
    "Theodor Adorno": [
        quip("Adorno picks one off -- joylessly, efficiently, with the air of a man who always suspected the whole spectacle was rotten. He's winning, and he hates that he's enjoying it.", when="overtake"),
        quip("Adorno climbs out looking thoroughly vindicated. Happiest when it all goes wrong.", when="incident"),
        quip("A clean, grim, optimal stop -- Adorno does the right thing and takes no pleasure in it. The pit lane's just the culture industry with tyre guns, far as he's concerned.", when="pit"),
    ],
    "Herbert Marcuse": [
        quip("Marcuse off on the attack -- the Great Refusal, except he never refuses a lunge.", when="start"),
        quip("Marcuse stays in it where everyone else lifted -- that's the Great Refusal made flesh. The corner says back out; he simply declines.", when="overtake"),
        quip("Refused to lift, refused to yield, refused the corner itself -- and the corner, this once, refused him right back. He won't mind. Refusing was the whole point.", when="incident"),
    ],
    "Michel Foucault": [
        quip("Foucault away well -- he reads a start the way he reads everything, watching where the others are pushed and slipping through where they aren't.", when="start"),
        quip("Foucault through on the line nobody else would touch -- the track herds you onto the obvious one, and he spends every lap taking the one it would rather he didn't.", when="overtake"),
        quip("Caught out probing for the line that isn't sanctioned -- he's forever testing where the real limits are. Found one of them, just then.", when="incident"),
        quip("Foucault boxes off the back of a read nobody else made -- he sees the whole board, every car, every window, and moves before the picture's even formed for the rest of them.", when="pit"),
    ],
    "Jacques Derrida": [
        quip("Derrida away, erratically as ever -- there's no one right line, he insists, so he'll try several, often in the same corner.", when="start"),
        quip("Derrida unpicks the man ahead -- finds the gap where the certainty about the racing line used to be, and is through it before anyone clocks it was ever there.", when="overtake"),
        quip("Derrida'd say the crash was always already happening. The marshals would say it's happening now.", when="incident"),
    ],
    "Frantz Fanon": [
        quip("Fanon away decisively -- never did wait politely for an opening.", when="start"),
        quip("Fanon takes it -- doesn't ask, doesn't wait to be granted the place. You seize your freedom out here; nobody hands it to you. That's his whole life in one move.", when="overtake"),
        quip("Fanon goes for one that wasn't quite on -- but he'd sooner overreach taking a place than sit meekly behind waiting for one to be offered. It never is.", when="incident"),
    ],
    "Aimé Césaire": [
        quip("Césaire away composed -- the measured one, the teacher. No fireworks off the line, just a man who knows exactly where this afternoon is going.", when="start"),
        quip("Césaire through, unhurried and clean -- he let the hotheads tear past and tear themselves up, wrote his own lap out longhand, and it proved the quicker for it.", when="overtake"),
        quip("Even the cool head gets it wrong sometimes -- a rare untidy moment from Césaire, and he'll be furious with himself in the most dignified possible way.", when="incident"),
        quip("A tidy, considered stop -- Césaire does nothing in a hurry and nothing twice. The plan was settled long before the board went out.", when="pit"),
    ],
    "Thomas Paine": [
        quip("Paine away straight and true -- no cunning, no theatre, just plain common sense pointed at Turn 1.", when="start"),
        quip("Paine forces it through -- no tricks to it, just plain courage plainly applied. Tends to be enough, he'd tell you, and just now it was.", when="overtake"),
        quip("Even common sense meets a gravel trap it can't argue with -- Paine overcooked that one, and there's no pamphlet that talks you out of a slide.", when="incident"),
        quip("A plain, honest stop -- no gamesmanship from Paine, just the sensible call made out in the open for anyone to see.", when="pit"),
    ],
    "Mary Wollstonecraft": [
        quip("Wollstonecraft away cleanly -- claims the place reason says is hers, and she's spent a lifetime arguing it was always hers to claim.", when="start"),
        quip("Wollstonecraft picks him off -- didn't out-muscle anyone, out-reasoned them; thought the braking zone through more clearly than the man ahead, and that was the whole pass.", when="overtake"),
        quip("Caught out there -- a rare lapse from one of the clearest heads on the grid. She'll have it diagnosed before she's back to the garage.", when="incident"),
        quip("A clear-eyed, principled stop -- Wollstonecraft reasons the plan out and commits to it. No sentiment in it, and she'd take that as the compliment it is.", when="pit"),
    ],
    "Ayn Rand": [
        quip("Rand away on her own terms -- won't draft, won't tuck in, won't take a tow off a soul. It looks heroic for about two corners.", when="start"),
        quip("Rand won't yield, won't draft, won't give an inch -- nearly gave the whole lot away there.", when="incident"),
        quip("And she's out. Wouldn't be told when to stop by the pit wall, so the wall told her instead.", when="retirement"),
    ],
    "Max Stirner": [
        quip("Stirner away, owing allegiance to nothing and no one -- least of all the racing line, which he regards as a polite fiction.", when="start"),
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
    quip("He's fine -- out of the car and gesturing philosophically, which is the international signal for 'it was the car.'", when="incident"),
    quip("In an infinite universe there is surely a track where that worked. This was not that track.", when="incident"),
    quip("He'll have a fully coherent account of why that wasn't his fault by the time he reaches the marshals.", when="incident"),
    quip("That is what we in the trade call 'a big one,' and what he'll call 'a learning experience.'", when="incident"),
    quip("The gravel, as ever, declines to engage with the argument.", when="incident"),
    quip("He has reduced a very expensive car to a very expensive lesson.", when="incident"),
    quip("The laws of physics remain undefeated, despite a spirited challenge from continental philosophy.", when="incident"),
    quip("Off into the scenery to reflect on his choices. He's got the time now.", when="incident"),
    quip("Not so much a corner as a difference of opinion -- which the corner won.", when="incident"),
    quip("A masterclass, that, in precisely how not to do it.", when="incident"),
    quip("Beautifully reasoned, all the way up to the bit where it met the barrier.", when="incident"),
    quip("He raised an objection with the apex. The apex was not taking questions.", when="incident"),
    quip("Spectacular. Awful, but spectacular. Chiefly awful.", when="incident"),
    quip("And there he sits, having out-thought everyone but the kerb.", when="incident"),
    quip("Profound. In the sense that he's now quite deep in the gravel.", when="incident"),
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
    quip("Gone -- like a footnote nobody read.", when="overtake"),
    quip("He'll want that referred to a committee. The committee has just driven off.", when="overtake"),
    quip("Resistance proved, in the end, both futile and slow.", when="overtake"),
    quip("Settled out of court, down the inside, no right of appeal.", when="overtake"),
    quip("There's a word for an argument you lose at the apex. The word is 'second.'", when="overtake"),
    quip("Two thousand years of thought, undone by a chap who simply braked later.", when="overtake"),
    quip("He had the better theory. The other one had the better exit.", when="overtake"),
    quip("Clean as you like. The loser's still drafting his reply.", when="overtake"),
    quip("Overtaken on merit, on the brakes, and on the balance of probabilities.", when="overtake"),
    quip("A profound objection, that. Noted, filed, and passed.", when="overtake"),
    quip("And the seminar's adjourned -- overtaken by events, and also by a car.", when="overtake"),
    quip("Magnificent. Somewhere a referee blows a whistle that does not exist.", when="overtake"),
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
    quip("Roughly four seconds, stationary, surrounded by people who all know better than him. He'll have HATED that.", when="pit"),
    quip("The undercut, the overcut, the stay-out-and-pray. Three plans, one of them right, and we'll know which in about eleven laps.", when="pit"),
    quip("There it is -- the one place on the circuit where the cleverest man alive has to sit still and trust a committee.", when="pit"),
    quip("Fresh tyres on. The car's faster, the wallet's lighter, and the gamble's away.", when="pit"),
    quip("A stop is just a wager you make at sixty miles an hour and pay off at the flag.", when="pit"),
    banter([
        ("pbp", "Talk me through it, Benny -- why now and not three laps ago?"),
        ("colour", "Track's come to them, tyres have gone off, and the gap behind's just big enough. Three laps ago it was a gamble; now it's arithmetic. Mostly."),
    ], when="pit"),
    banter([
        ("pbp", "And is that the right call?"),
        ("colour", "Ask me at the flag. That's the maddening beauty of a pit stop -- you only ever find out you were right once it's too late to be wrong."),
    ], when="pit"),
]


# =============================================================================
# THE CALLS -- the lap caller's FACTUAL lines, as data. Spoken prose; any number
# is spelled by colour.py before it airs. Placeholders: {driver}, {other},
# {at} (=" at <corner>" or ""), {pos} (a spelled ordinal -- "second"),
# {gained} (a spelled cardinal -- "four"), {stint} (spelled), {earlier}.
# Pools are deep and the booth never repeats one back-to-back, so the busiest
# afternoon of passing and stopping never reads from a script.
# =============================================================================

# =============================================================================
# THE DUO TEXTURE -- measured from a real two-man booth (dev analysis, not shipped).
# Three findings drive these pools:
#   * The colour man reasons and JUDGES -- he leans on opinion ("I think", "for my
#     money") and causal openers ("so", "now", "see"). The lap caller does neither.
#   * The lead caller REPORTS, never editorialises -- when he takes the ball back
#     after a reaction, it's a flat factual closer, not a verdict.
#   * The lead is the only one who holds a long solo: an extended set-piece build
#     when the race is on the line. The colour man never holds court that long.
# These lift the FLAT single-line reactions toward that shape. The hand-authored
# PAIR_LORE exchanges already have it, and are left alone.
# =============================================================================

# Benny leads a reaction with his own register -- an opinion or a causal "watch this".
# Prepended to a plain colour line to turn a zinger into a read. Phill never uses these.
BENNY_VERDICT = [
    "I'll tell you what --",
    "For my money --",
    "Mind you --",
    "See, that's the thing --",
    "So watch this --",
    "Now, this is the bit --",
]

# Phill reclaims the call after Benny's word -- short, factual, no opinion. This is
# what makes the handoff read both ways (caller -> colour -> caller), the even
# back-and-forth a real booth runs. Matches his clipped in-exchange voice.
PHILL_RECLAIM = [
    "And the place is held.",
    "Done, and they race on.",
    "Through, and gone.",
    "Order settled -- for now.",
    "On to the next, then.",
    "And up the road they go.",
    "That's that one done.",
]

# Phill's set-piece: an extended solo build for a genuine nail-biter in the closing
# laps -- the lead caller running, uninterrupted, the way the real booth lets him.
# Each entry is a 2-3 line build using {count}, {ldr}, {sec}. Factual and escalating,
# never a verdict -- the tension comes from the race, not from an opinion about it.
RUNIN_SETPIECE = [
    ["{count} -- and {sec} is right with {ldr} now, glued to the back of them.",
     "Into the final sequence, {sec} looking for a way, {ldr} covering every line --",
     "-- and this is going to the flag!"],
    ["{count}, and the gap is nothing. {ldr} leads, {sec} hunting.",
     "Every corner now, {sec} is closer -- {ldr} has nowhere to hide and nothing in hand.",
     "We are going to settle this on the last lap!"],
    ["{count} -- {ldr} from {sec}, and you can throw a blanket over them.",
     "{sec} has a run! Down towards the braking zone, side by side --",
     "-- and they go through together, still nothing in it!"],
    ["{count}. {ldr} out front, {sec} all over the back of the car.",
     "This is flat out, both of them, not a tenth to spare anywhere on the lap --",
     "-- and the crowd are on their feet for the run to the line!"],
]

# Getaways off the line, by how big the launch was.
START_CALLS = {
    "lead": ["{driver} BEATS them all off the line -- leads into Turn 1!",
             "Lights out -- and it's {driver} who gets the jump to lead them away!",
             "A mighty launch from {driver} -- into Turn 1 with the lead!",
             "{driver} nails the start and sweeps into the lead at the first corner!"],
    "flier": ["{driver} -- what a launch! Storms up to {pos}!",
              "{driver} is away like a scalded cat -- up to {pos} already!",
              "Sensational getaway from {driver} -- {gained} places gained, up to {pos}!",
              "Where did {driver} come from?! A rocket off the line, up to {pos}!",
              "{driver} launches off the rail and absolutely BUFFETS through -- up to {pos}!",
              "Oh, {driver} has nailed it -- {gained} places in three hundred metres, up to {pos}!"],
    "good": ["{driver} gets a flier off the line, up to {pos}.",
             "Good launch from {driver} -- slots into {pos} through Turn 1.",
             "{driver} makes a couple off the start, up into {pos}.",
             "Tidy getaway, {driver} -- gains a place or two, up to {pos}.",
             "Clean and quick away, {driver}, up to {pos}.",
             "{driver} times the lights nicely -- up to {pos}."],
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
             "The move for the lead! {driver} clears {other}{at} and hits the front!",
             "{driver} goes around the OUTSIDE of {other}{at} -- and leads the Grand Prix!",
             "We have a new leader! {driver} muscles past {other}{at} and into the lead!",
             "{driver} sends it{at} -- {other} has no answer, and it's a new race leader!"],
    "podium": ["{driver} forces it past {other}{at} for {pos}!",
               "{driver} dives past {other}{at} -- up to {pos}!",
               "Lovely move by {driver}{at}, clears {other} for {pos}!",
               "{driver} won't be denied{at} -- through on {other} for {pos}!",
               "{driver} has {other} for {pos}{at} -- and it's done cleanly!",
               "{driver} throws it up the inside of {other}{at} and grabs {pos}!",
               "Brave from {driver}{at} -- around {other} and into {pos}!",
               "{driver} times it to perfection{at}, past {other} for {pos}!"],
    "points": ["{driver} gets the move done on {other}{at}, up to {pos}.",
               "{driver} picks off {other}{at} -- into {pos}.",
               "{driver} makes it past {other}{at} for {pos}.",
               "A place gained for {driver}{at}, ahead of {other} into {pos}.",
               "{driver} slots past {other}{at} and up to {pos}.",
               "{driver} finds a way by {other}{at} -- {pos} now.",
               "{driver} lines up {other}{at} and is through for {pos}.",
               "Down the inside goes {driver}{at} -- ahead of {other}, into {pos}.",
               "{driver} eases past {other}{at} and into {pos}.",
               "Job done for {driver}{at} -- {other} dealt with, up to {pos}."],
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

# The CALLBACK: a fight that went quiet several laps ago flares up again. This is the
# director's MEMORY made audible -- it only fires when the narrative layer recognises
# a pair it has seen scrapping before, after enough of a lull that "again" would be a
# lie. {ago} is the spelled number of laps since they last traded. (See director.py.)
BATTLE_REIGNITE = [
    "These two AGAIN! {driver} and {other} were at this {ago} laps back -- and here we go once more!",
    "We have seen this fight before! {driver} renews it with {other}{at} -- the rematch is ON!",
    "Remember these two earlier? That simmering scrap from {ago} laps ago reignites -- {driver} back ahead of {other}!",
    "Round two -- {driver} and {other} pick up exactly where they left off, and it's {driver} in front!",
    "Back on it! The battle between {driver} and {other} we saw {ago} laps ago has flared right back up!",
]

# The two ways a tracked fight can END across event types -- the director recognises
# the pair and reaches for these (see director.py). CONTACT is a lead-in: the booth's
# normal collision call (who's actually out) follows it. UNDERCUT is a standalone
# call -- it replaces the plain undercut line when the move settles a fight the cars
# couldn't resolve on track.
BATTLE_CONTACT = [
    "And it's ended in CONTACT! That fight between {driver} and {other} has finally boiled over{at}!",
    "There it is -- the scrap we've been watching ends in tears! {driver} and {other} collide{at}!",
    "They couldn't keep doing this forever -- {driver} and {other} come together{at}, and the battle is OVER!",
    "Too close for too long -- and {driver} and {other} make contact at last{at}!",
]
BATTLE_UNDERCUT = [
    "And the fight is settled in the PIT LANE! {driver} couldn't pass {other} on track -- so the undercut does it, into {pos}!",
    "{driver} beats {other} the only way left after all those laps stuck behind -- a clean undercut, up into {pos}!",
    "Couldn't do it wheel-to-wheel, so {driver} does it on the pit wall! Ahead of {other} and into {pos}!",
    "That's how you break a deadlock! {driver} undercuts {other} -- the fight they couldn't win on track, won in the stops, into {pos}!",
]

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
    # The GENUINE first stop of the race -- the dam breaks, the strategic game opens.
    # Only used for the first stop the booth calls all race (see call_pit), so the
    # "first to blink" claim is always true.
    "race_first": ["And {driver} blinks first -- the first stop of the race, in they come{onto}.",
                   "{driver} is first to crack -- into the lane{onto}, and the stops are under way.",
                   "Here come the stops! {driver} blinks first{onto} -- the strategic game begins.",
                   "{driver} breaks cover first{onto} -- the first to commit, and the undercut chess starts here.",
                   "There's the first move of the race -- {driver} into the pit lane{onto} ahead of everyone."],
    # A driver's OWN first stop, AFTER others have already been in -- no "first" claim,
    # because they are not first; they are simply making their first stop.
    "first": ["{driver} peels into the pit lane{onto}.",
              "{driver} comes in to serve the stop{onto}.",
              "Box, box for {driver} -- in for service{onto}.",
              "{driver} dives into the lane after a {stint}-lap opening stint{onto}.",
              "And {driver} comes in for the first time{onto}.",
              "{driver} ends the opening stint -- into the lane{onto}."],
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


# --- THE STEWARDS -- Phill's factual penalty calls, as data ------------------
# A penalty's broadcast arc: the NOTICE (under investigation), the VERDICT (a
# kind and a number), the SERVING (a drive-through), and -- when it's served at
# the flag -- the RECLASSIFICATION. Numbers spelled by colour.py before they air.
INVESTIGATION_CALLS = {
    "avoidable contact": [
        "The stewards are taking a look at that contact between {driver} and {other}.",
        "That one's going upstairs -- {driver} and {other}, under investigation.",
        "Note from race control: the {driver}-{other} incident is under investigation.",
        "{driver} into {other} -- and the stewards have flagged it for a look.",
        "Race control will review that one -- {driver} and {other}, noted.",
    ],
    "pit-lane speeding": [
        "Race control are checking {driver}'s speed through the pit lane.",
        "{driver} may have been a shade quick in the lane -- under investigation.",
        "The pit-lane gun has {driver} under review.",
    ],
    "unsafe release": [
        "Questions over {driver}'s release from the box -- the stewards are looking.",
        "That looked a tight release for {driver} -- under investigation.",
    ],
    "jump start": [
        "The lights -- and the stewards are checking {driver}'s getaway.",
        "Did {driver} go early? A possible jump start, under investigation.",
    ],
}
PENALTY_CALLS = {
    "time": [
        "And the verdict: a {secs}-second penalty for {driver}, for {offence_phrase}.",
        "{driver} gets {secs} seconds -- {offence_phrase}, say the stewards.",
        "The stewards have decided: {secs} seconds for {driver}, for {offence_phrase}.",
        "Penalty for {driver} -- {secs} seconds, for {offence_phrase}.",
        "There it is -- {secs} seconds for {driver}, the stewards pinning it on {offence_phrase}.",
    ],
    "drive-through": [
        "Worse for {driver} -- a drive-through, for {offence_phrase}.",
        "The stewards throw the book at {driver}: a drive-through, for {offence_phrase}.",
        "{driver} handed a drive-through for {offence_phrase} -- and that genuinely hurts.",
    ],
    "stop-go": [
        "A ten-second stop-go for {driver}, for {offence_phrase} -- about as bad as it gets short of the black flag.",
        "Stop-go for {driver}, for {offence_phrase}. Sit in the box for ten and think it over.",
    ],
    "dsq": [
        "And {driver} is OUT -- disqualified for {offence_phrase}. Extraordinary scenes.",
        "The black flag for {driver} -- disqualified for {offence_phrase}. Their afternoon ends in the stewards' room.",
    ],
    "warning": [
        "Black-and-white flag for {driver} -- a warning for {offence_phrase}. One more and it's a penalty.",
        "{driver} shown the black-and-white -- final warning for {offence_phrase}.",
    ],
}
PENALTY_SERVED_CALLS = [
    "{driver} peels in to serve it -- straight down the lane, no new rubber.",
    "There goes {driver} to take the medicine -- penalty served.",
    "{driver} serves it: a long, lonely trip down the pit lane and out the far end.",
]
RECLASSIFICATION_CALLS = [
    "{driver} crosses the line {prov} -- but the penalty drops them to {off}.",
    "And the stewards have the final word: {driver} classified {off}, not {prov}.",
    "On the road it was {prov} for {driver} -- on the timing sheet, the penalty makes it {off}.",
]

# Benny's colour on a verdict -- what it MEANS for the race, dry and to the point.
# Generic (any driver), so deliberately gender-neutral, like the other shared pools.
PENALTY_COLOUR = [
    quip("Five seconds doesn't sound much until you remember it's about a year and a half out here.", when="penalty"),
    quip("That's the undercut dead in the water -- they've the gap to find AND the penalty to serve, at the same stop.", when="penalty"),
    quip("Now the maths gets cruel: they have to build a five-second buffer, or they're serving it at the flag and dropping like a stone.", when="penalty"),
    quip("Track position they earned on the road, handed straight back in the stewards' room.", when="penalty"),
    quip("They'll serve it at the stop -- so the crew get five extra seconds to admire their handiwork. [chuckle]", when="penalty"),
    banter([("pbp", "How much does that cost them, Benny?"),
            ("colour", "A podium becomes a points finish, just like that. They can't just race the car ahead now -- they have to beat it by five seconds, which is a different sport.")], when="penalty"),
    banter([("pbp", "Can they recover from that?"),
            ("colour", "Only by doing on track what the stewards just undid on paper. Pit with a cushion, or cross the line far enough clear that the penalty doesn't matter. Easy to say at this end of the pit wall.")], when="penalty"),
    quip("And there's the thing about justice at two hundred miles an hour -- it arrives three laps after the crime and lands on the timing screen. [sigh]", when="penalty"),
]


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
        banter([("colour", "Marx past Stirner. He once wrote three hundred pages just to tell this fella he was wrong. [chuckle]"),
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
    # Teammates who agree on the cause and nothing else -- the family argument, at speed.
    ("Rosa Luxemburg", "Karl Marx"): [
        banter([("colour", "Luxemburg past her own man Marx! She spent her life telling his followers the plan would arrive on its own if they'd only wait -- and that waiting was the one thing she'd never do."),
                ("pbp", "And she didn't wait there."),
                ("colour", "Took the gap the moment it opened. He'd have let it develop for another ten laps. That's the whole quarrel in one corner.")], when="overtake"),
    ],
    ("Karl Marx", "Rosa Luxemburg"): [
        quip("Marx reels his own teammate back in -- the long game past the quick one. Patience, he'd tell Luxemburg, history rewards the side that can wait. She's never believed a word of it.", when="overtake"),
    ],
    ("Emma Goldman", "Mikhail Bakunin"): [
        banter([("colour", "Goldman past Bakunin -- no masters on this team, and that includes each other."),
                ("pbp", "No holding station, then."),
                ("colour", "She'd be insulted to be asked, and he'd be insulted to ask. Two anarchists racing flat out is the only honest arrangement they've got.")], when="overtake"),
    ],
    ("Mikhail Bakunin", "Emma Goldman"): [
        quip("Bakunin barges past his own teammate -- no gods, no masters, no team orders, and apparently no exceptions for Goldman either. She'd have it no other way.", when="overtake"),
    ],
    ("Simone de Beauvoir", "Friedrich Nietzsche"): [
        banter([("colour", "de Beauvoir past Nietzsche -- and there's a lineage there. She took his idea that you make yourself out of nothing handed down."),
                ("pbp", "But?"),
                ("colour", "But she never forgot the car, the grid, the situation you start from -- the bit he sailed straight past. Accounted for all of it, and beat him to the corner.")], when="overtake"),
    ],
    ("Friedrich Nietzsche", "Simone de Beauvoir"): [
        quip("Nietzsche storms past de Beauvoir -- pure will, no account taken of where anyone started or what they were carrying. It's reckless, it's magnificent, and it's exactly the blind spot she spent a career naming.", when="overtake"),
    ],
    ("Niccolò Machiavelli", "Richard Rorty"): [
        quip("Machiavelli past his teammate Rorty -- two men who long ago stopped asking what the 'true' racing line is and started asking only what works. Today, cunning worked.", when="overtake"),
    ],
    ("Richard Rorty", "Niccolò Machiavelli"): [
        quip("Rorty does his own strategist Machiavelli -- no grand scheme to it, just the line that kept paying off, lap after lap, until it paid off past the Prince himself.", when="overtake"),
    ],
    ("Herbert Marcuse", "Theodor Adorno"): [
        banter([("colour", "Marcuse past Adorno -- the old Frankfurt split, replayed at the apex. When the students rose up, one of these two went to the barricades and the other went to the telephone."),
                ("pbp", "Marcuse to the barricades."),
                ("colour", "Every time. Adorno analyses the corner; Marcuse takes it. That's the difference, and there it goes by.")], when="overtake"),
    ],
    ("Jacques Derrida", "Plato"): [
        banter([("colour", "Derrida past Plato! He built an entire career taking the old man's certainties apart, line by line."),
                ("pbp", "And now the racing line."),
                ("colour", "Found the crack in the one Plato swore was perfect, and slipped clean through it. The dreamer's been deconstructed.")], when="overtake"),
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


# When a quiet-lap discussion is PARKED by the racing (a pass, a crash, a rundown)
# and the booth picks it back up several laps later, it re-establishes the subject
# FIRST -- otherwise the resumed beat ("And out here?", "So a Grand Prix is--")
# assumes a context the listener lost laps ago and reads as a non-sequitur. Phill
# says one of these as a re-entry, then the thread continues. {names} is the
# thread's subjects, as surnames a caller would actually say ("Derrida and Rorty").
CHATTER_RESUME_NAMED = [
    "Back to {names}, then -- where the racing cut us off.",
    "Now there's a breather: we were on about {names} a few laps back.",
    "Returning to {names} for a moment, before all that interrupted us.",
    "Where were we... {names}, that was it.",
    "So, picking {names} back up, where we left it.",
    "And we never finished on {names}, did we -- let's put that right.",
    "Right -- {names}, before the race so rudely intervened.",
]
# The same re-entry, for a general thread with no named driver to anchor it.
CHATTER_RESUME_GENERIC = [
    "Now, where were we -- before the racing got in the way.",
    "Right, picking up where we left off a few laps back.",
    "Let me finish that thought, now there's a breather.",
    "Back to what we were chewing over earlier.",
]


DISCUSSIONS = [

    # --- single thinkers: what actually drives them ------------------------
    discussion([
        ("pbp", "For anyone new to this, Benny -- what actually drives Nietzsche out there?"),
        ("colour", "The will to power. And it's not what folk think -- it's not bossing people about."),
        ("pbp", "No?"),
        ("colour", "It's the drive in everything alive to grow, to overcome, to become MORE than it was. He'd say a tree doesn't grow to survive -- it grows to be a bigger tree."),
        ("pbp", "Which on a flying lap--"),
        ("colour", "--is a man never satisfied, always reaching past the limit. Thrilling to watch. [chuckle] Nightmare to put a delta time in front of."),
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
        ("colour", "Never. And his racecraft's the same -- no theory, just send it and embarrass the cleverer bloke. Told Alexander the Great once to get out of his light. To his face. [chuckle]"),
    ], about=("Diogenes",), topic="the cynic"),

    discussion([
        ("pbp", "Machiavelli, reading the race three moves ahead as ever."),
        ("colour", "The original strategist. People hear 'Machiavellian' and think villain -- but he was just honest about how power actually works, not how we'd like it to."),
        ("pbp", "The ends justify the means."),
        ("colour", "More like: judge a leader by results, not intentions. That's the pit wall's creed exactly. He'd undercut his own grandmother and send a lovely card after. [chuckle]"),
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
        ("colour", "--exhibit A. Bread and circuits. Mind you, this is the man who, when actual students occupied his lecture hall, called the police. Radical on paper, less so in the corridor. [chuckle]"),
    ], about=("Theodor Adorno",), topic="culture industry"),

    discussion([
        ("pbp", "Plato out front, driving to some ideal."),
        ("colour", "Literally. He reckoned everything down here's a shadow of a perfect Form up in the realm of ideas -- a perfect circle, perfect justice, perfect lap."),
        ("pbp", "And the philosopher-king?"),
        ("colour", "His fix for politics: let the wisest rule. Funny how the man proposing it was always quite sure who the wisest was. Same energy as a driver certain the team should be built round him. [chuckle]"),
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
        ("colour", "--is just another ghost. He owns himself, nothing owns him -- including the strategy that'd actually get him home. Marx wrote a whole book tearing him apart. Stirner barely noticed. [chuckle]"),
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
        ("pbp", "The Objectivism pair, Rand and Stirner -- two of a kind?"),
        ("colour", "Both worship the self, but they can't stand each other really. Rand built rules around her egoism -- reason, rights, a whole system."),
        ("pbp", "And Stirner?"),
        ("colour", "Thought rules were for ghosts. No system, no morality, nothing sacred but himself. Rand was horrified to be filed next to him. Two self-made men, neither will finish. Poetic, that. [sigh]")
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
        ("colour", "Everything, ideally. That's why we get up in the morning, Phill."),
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
        ("pbp", "Stirner and his 'spooks' -- and for anyone who hasn't waded through The Ego and Its Own, Benny, give them the proper version, because it's better than it sounds."),
        ("colour", "It's his word for any grand abstraction you let boss you about. The State. Morality. Humanity. God. Ghosts, he says -- real only because you bow to them. Stop bowing and they vanish."),
        ("pbp", "Which is a marvellous theory right up until a blue flag, I'd have thought."),
        ("colour", "Especially the blue flag. He'd treat it as a haunting. Which is precisely why he and Rand are sat in the gravel debating property rights with a marshal."),
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

    # === NEW WAVE: how the theories play off one another (Phill draws Benny out) ===
    discussion([
        ("pbp", "Marx and Rand on the same circuit, Benny. I can't imagine they'd agree on the time of day."),
        ("colour", "They wouldn't agree on whether there IS a time of day. Marx says you are made by the collective, the class, the conditions. Rand says the collective is a mob with a flag, and the only thing that's real is the individual who refuses it."),
        ("pbp", "And on track that looks like--?"),
        ("colour", "Marx nursing the tyres for the good of a race plan nobody clapped, and Rand refusing a single instruction on principle and parking it in the wall. One of them finishes. It is never her."),
    ], about=("Karl Marx", "Ayn Rand"), topic="marx vs rand"),

    discussion([
        ("pbp", "People forget Marx actually wrote about Stirner -- and at LENGTH."),
        ("colour", "Pages and pages. 'Saint Max,' he called him, in this enormous sarcastic demolition -- spent more words ridiculing Stirner's ego than Stirner ever spent having one. The biggest takedown in the history of thought, of a man almost nobody had read."),
        ("pbp", "Overkill."),
        ("colour", "Magnificent overkill. Like bringing a wrecking ball to a game of conkers. And here they are sharing a track, Marx still faintly furious, Stirner serenely unbothered because to him Marx is just another spook."),
    ], about=("Karl Marx", "Max Stirner"), topic="marx vs stirner"),

    discussion([
        ("pbp", "Foucault and Marx -- both on the left, but they read power completely differently, don't they."),
        ("colour", "Chalk and very clever cheese. Marx says power runs top-down from who owns the factory. Foucault says no -- it's everywhere, in the timing screen, the medical, the stewards' noticeboard, the little rules that shape you before anyone gives an order."),
        ("pbp", "So who'd Foucault watch?"),
        ("colour", "The marshals, not the leader. He'd say the race is won by whoever the SYSTEM was quietly built to reward -- and then he'd find that fascinating rather than do anything about it. Marx would want to know who owns the grandstand."),
    ], about=("Michel Foucault", "Karl Marx"), topic="foucault vs marx"),

    discussion([
        ("pbp", "Rorty and Plato -- two and a half thousand years apart, and Rorty spent his career arguing with him."),
        ("colour", "Plato started the whole game: there's a perfect true world behind this shabby one, and thinking means mirroring it. Rorty said that's the original sin of philosophy -- there's no mirror, no God's-eye view, just us muddling along with better and worse descriptions."),
        ("pbp", "So the racing line--"),
        ("colour", "--Plato chases the one PERFECT line that exists in heaven. Rorty just wants the line that's quick today on these tyres. And the maddening thing is Rorty's usually the faster way round. Don't tell Plato."),
    ], about=("Richard Rorty", "Plato"), topic="rorty vs plato"),

    discussion([
        ("pbp", "Machiavelli and Plato, then -- the realist and the idealist, side by side."),
        ("colour", "The whole argument of politics in two cars. Plato designs the ideal race and the ideal driver to run it. Machiavelli says lovely, now here's how races are ACTUALLY won, by people who are tired and frightened and occasionally cheating."),
        ("pbp", "Ought versus is."),
        ("colour", "Exactly that. Plato races the track as it should be; Machiavelli races it as it is. One of them keeps getting surprised by the weather. It is not the Florentine."),
    ], about=("Niccolò Machiavelli", "Plato"), topic="machiavelli vs plato"),

    discussion([
        ("pbp", "Paine and Wollstonecraft -- now THERE'S an alliance rather than a feud."),
        ("colour", "Comrades, these two. Same city, same circle, both picked up their pens to answer the same grumpy conservative -- Paine with the Rights of Man, Wollstonecraft with the Rights of Woman, a year apart. Two pamphlets that between them sketched the modern world."),
        ("pbp", "You can see the kinship on track."),
        ("colour", "Plain, fearless, no cunning in either of them -- they just point the car at what's right and go. If the grid had a conscience, it'd be these two. Sadly the grid mostly has an ego."),
    ], about=("Thomas Paine", "Mary Wollstonecraft"), topic="paine and wollstonecraft"),

    discussion([
        ("pbp", "Diogenes and Rand -- both wave the flag for the individual, and yet."),
        ("colour", "Opposite ends of the same stick. Rand's individual OWNS things -- the achievement, the building, the trophy, and good luck prising them off her. Diogenes owned a barrel, gave away his only cup when he saw a boy drink from his hands, and was happier than the lot of them."),
        ("pbp", "Same word, two religions."),
        ("colour", "Completely. Tell Rand the highest freedom is needing nothing and she'd be appalled. Tell Diogenes the highest freedom is a property portfolio and he'd laugh himself off the barrel. They'd both call the other a fraud, and honestly, grab the popcorn."),
    ], about=("Diogenes", "Ayn Rand"), topic="diogenes vs rand"),

    discussion([
        ("pbp", "Nietzsche and Rorty -- both knock the legs out from under 'Truth,' don't they. But they're not the same."),
        ("colour", "Same demolition, very different mood. Nietzsche tears down the old certainties and it's THUNDER -- create your own values or perish, the lonely hero on the mountain. Rorty tears down the same certainties and it's a man at a barbecue going, ah well, let's just be kind and see what works."),
        ("pbp", "Cheerful nihilism versus heroic nihilism."),
        ("colour", "And neither's really nihilism, but don't tell the internet. Out here Nietzsche drives like the fate of mankind's on it. Rorty drives like it's a nice day for a drive. Both quick. Only one needs a lie down after."),
    ], about=("Friedrich Nietzsche", "Richard Rorty"), topic="nietzsche vs rorty"),

    discussion([
        ("pbp", "I have to raise it, Benny -- Nietzsche on women was, let's say, not his finest hour, and Wollstonecraft is right there."),
        ("colour", "Not his finest decade, that. Said some genuinely daft and ugly things about women -- the 'whip' line and worse. No defending it, and I won't. And then you put him on a circuit with Mary Wollstonecraft, who built the entire rational case that he's talking rot."),
        ("pbp", "She is the rebuttal."),
        ("colour", "She's the rebuttal in a racing car. Give people reason and a fair chance, she said, and watch them go -- and there she is, going, right past a man who theorised she couldn't. The track keeps no opinions, only lap times. Hers are good."),
    ], about=("Friedrich Nietzsche", "Mary Wollstonecraft"), topic="nietzsche vs wollstonecraft"),

    discussion([
        ("pbp", "Adorno and Rorty would NOT have got on, would they."),
        ("colour", "Oil and water, and the water's doing a little dance. Adorno looks at modern life and sees a beautifully engineered trap and despairs in four hundred pages. Rorty looks at the same thing, shrugs, and says well, it could be kinder, let's try that."),
        ("pbp", "Pessimist meets optimist."),
        ("colour", "And they'd each find the other unbearable -- Adorno thinks Rorty's a naive American smiling at a fire, Rorty thinks Adorno's enjoying the gloom too much to put it out. Watch them in the wet: one suffers gloriously, one just gets on with it."),
    ], about=("Theodor Adorno", "Richard Rorty"), topic="adorno vs rorty"),

    discussion([
        ("pbp", "Luxemburg and Bakunin -- both can't stand being told what to do, but they're not the same animal."),
        ("colour", "No. Bakunin wants to smash the state full stop, no plan, trust the rubble. Luxemburg's still a Marxist -- she wants the workers to run things -- but she trusts the spontaneous mass over any central committee. Her line: freedom is always the freedom of the one who thinks differently."),
        ("pbp", "So a different kind of fearless."),
        ("colour", "Bakunin's fearless like a fire. Luxemburg's fearless like someone who's read everything, decided anyway, and is already three corners up the road while the committee's still taking minutes."),
    ], about=("Rosa Luxemburg", "Mikhail Bakunin"), topic="luxemburg vs bakunin"),

    discussion([
        ("pbp", "Marcuse and Rand -- the Great Refusal versus the virtue of selfishness."),
        ("colour", "Two people who'd refuse to share a podium, for opposite reasons. Marcuse says the system buys you off with comforts so you stop resisting -- so refuse, say no, want more than they're selling. Rand says the system's only crime is daring to ask you to share."),
        ("pbp", "Both refusers, then."),
        ("colour", "Both magnificent refusers. Marcuse refuses for everyone; Rand refuses on behalf of herself and is faintly annoyed there's a herd watching. Put them on track and they both attack -- and you genuinely can't tell whether they're allies or about to collect each other at the chicane."),
    ], about=("Herbert Marcuse", "Ayn Rand"), topic="marcuse vs rand"),

    discussion([
        ("pbp", "Derrida and Rorty -- both say there's no solid floor under our words, but they could not SOUND more different."),
        ("colour", "Same destination, opposite vehicles. Derrida takes forty dense pages to show meaning never quite settles. Rorty says 'yeah, words are tools, use the ones that work' and goes for lunch. One of them you need a seminar to follow; the other you could explain to a labrador."),
        ("pbp", "And on the track?"),
        ("colour", "Derrida deconstructs the racing line until there isn't one and ends up in the gravel being interesting about it. Rorty just drives the line that's working. The pragmatist beats the post-structuralist to the flag, then politely declines to call it Truth."),
    ], about=("Jacques Derrida", "Richard Rorty"), topic="derrida vs rorty"),

    discussion([
        ("pbp", "Nietzsche and Marx -- the two biggest hammers of the nineteenth century, and they swing at totally different things."),
        ("colour", "They do. Marx says history's engine is the MATERIAL -- who owns what, who works for whom. Nietzsche says it's the WILL -- the drive in the individual to overcome, to become more. Class versus the lonely self, basically."),
        ("pbp", "So they'd read this race--"),
        ("colour", "--completely differently. Marx points at the constructors' budgets and says there's your result, written before lights-out. Nietzsche points at one driver going flat where everyone lifts and says no, THERE'S your result. Annoyingly, on any given Sunday, either of them might be right."),
    ], about=("Friedrich Nietzsche", "Karl Marx"), topic="nietzsche vs marx"),

    # === thematic: the philosophy OF racing, with the booth's daft streak showing ===
    discussion([
        ("pbp", "Here's one for you, Benny. If a driver spins in the forest at Spa and no camera sees it, did it happen?"),
        ("colour", "The stewards say yes, the driver says no, and the philosopher says 'define happen.' Meanwhile the gravel has already formed a strong and lasting opinion."),
        ("pbp", "So it's settled."),
        ("colour", "Everything's settled, Phill, by the gravel. It's the most decisive thing in the paddock. No footnotes, no appeals, just consequences. We should put it in charge."),
    ], topic="tree in the forest"),

    discussion([
        ("pbp", "Do any of them ever agree on anything?"),
        ("colour", "Once a season, by accident, two of them concur and immediately get suspicious of each other for it. Twenty people who built their whole lives on never conceding a point, asked to share one braking zone."),
        ("pbp", "Recipe for disaster."),
        ("colour", "Recipe for OUR mortgage, is what it is. If they ever did agree we'd be out of a job and they'd be out of a reason to live. Long may they squabble."),
    ], topic="do they ever agree"),


    discussion([
        ("pbp", "Walk the listener through an undercut properly, Benny -- it sounds like magic and it isn't."),
        ("colour", "No magic at all. You pit before the car ahead, bolt on fresh tyres, and for two or three laps you're flying while they're crawling on old rubber. By the time THEY stop, you've banked enough time to come out in front. You overtake them in the pit lane without ever touching them on track."),
        ("pbp", "A pass you make with arithmetic."),
        ("colour", "A pass you make with a calculator and a bit of nerve. Machiavelli's favourite kind of move -- you beat a man who never sees you coming and is cross about it for a week."),
    ], topic="explainer: undercut"),

    discussion([
        ("pbp", "And the tyres, for anyone new to this -- why all the fuss?"),
        ("colour", "Because they're the only bit of the car touching the road, and they wear out. Softer rubber's faster but dies young; harder lasts but you give away pace. The whole strategy is just managing a slow, expensive heartbreak."),
        ("pbp", "Put like that it's almost philosophy."),
        ("colour", "It IS philosophy, Phill -- it's mortality with a pit board. Everything good out here is running out the moment it starts. Marx would tell you that's true of capitalism. Nietzsche would tell you to love it anyway. I'd tell you it's lap eighteen and the softs are gone."),
    ], topic="explainer: tyres"),


    discussion([
        ("pbp", "You always say the gravel trap's the real philosopher out here."),
        ("colour", "It's the only honest one. The cleverest man alive can argue that the corner doesn't really exist, that grip is a social construct, that the wall is a text open to interpretation -- and the gravel just sits there going, mm, lovely, in you come."),
        ("pbp", "Undefeated."),
        ("colour", "Never lost an argument in its life. If there's a final truth in this sport, it's beige, it's about a foot deep, and it's just past the exit kerb at every corner on Earth."),
    ], topic="the gravel philosopher"),

    discussion([
        ("pbp", "What would this lot make of LOSING, do you reckon? Properly losing."),
        ("colour", "Oh, every one of them's got it pre-rationalised. Nietzsche calls it overcoming-in-waiting. Marx calls it the system. Rand calls it sabotage by lesser men. Adorno expected it and feels grimly vindicated."),
        ("pbp", "Nobody just says 'I was slower'?"),
        ("colour", "Paine might. Possibly Wollstonecraft, through gritted teeth. The other eighteen would sooner rewrite the philosophy of the universe than admit the other chap braked later. It's why we love them."),
    ], topic="on losing"),

    discussion([
        ("pbp", "If you had to put one of them in charge of the rulebook, who?"),
        ("colour", "Dear God, not one of THIS lot. Machiavelli would write rules that only benefit Machiavelli. The anarchists would eat the rulebook on principle. Plato would ban anyone who couldn't define 'overtaking.'"),
        ("pbp", "So nobody."),
        ("colour", "So the gravel. We keep coming back to the gravel, Phill. I'm starting to find it a bit spiritual, if I'm honest, and I'd like that noted before I retire."),
    ], topic="who writes the rules"),

    # === a thinker AND this circuit (more of the booth's local knowledge) ===
    discussion([
        ("pbp", "Foucault at Suzuka -- the figure-of-eight, the track that watches itself."),
        ("colour", "Oh, he'd adore this place. A circuit that literally crosses over itself, where you're always being observed from the other half of the lap. Foucault built a whole theory out of being watched into good behaviour -- and here's a track that does it with a bridge."),
        ("pbp", "Made for him."),
        ("colour", "Tailor-made. Everyone else sees a racetrack; Foucault sees the most honest building in the sport -- one that admits it's keeping an eye on you. He'd lap it beautifully and write three hundred pages about the marshals' towers."),
    ], about=("Michel Foucault",), track="Suzuka", topic="foucault at suzuka"),

    discussion([
        ("pbp", "Rorty at Silverstone, fast and old and unpretentious."),
        ("colour", "His kind of place. No mystique, no cathedral -- an old airfield where the corners just work or they don't. Rorty had no time for the sacred; he'd love a track that's quick because it's quick, not because anyone wrote a poem about it."),
        ("pbp", "Does the job."),
        ("colour", "Does the job, asks no questions. Maggotts and Becketts don't care about your theory of truth -- get them right or don't. Rorty would call that the most honest philosophy lesson on the calendar, and then have a cup of tea about it."),
    ], about=("Richard Rorty",), track="Silverstone", topic="rorty at silverstone"),

    discussion([
        ("pbp", "Adorno at Monaco. The culture-industry man, in the most photographed square mile on Earth."),
        ("colour", "He's in physical pain, Phill, and loving it. A billion in boats, champagne on every balcony, the whole thing a glittering advert for itself -- Adorno coined 'the culture industry' for precisely this, mass spectacle that keeps everyone pleasantly docile."),
        ("pbp", "So he hates it."),
        ("colour", "He hates it the way a man hates being proved right. Every yacht's a footnote in a book he already wrote. He'll do the whole race scowling, finish fourth, and call it commodified disappointment. Marvellous value, Adorno."),
    ], about=("Theodor Adorno",), track="Monte Carlo", topic="adorno at monaco"),

    discussion([
        ("pbp", "Fanon at Interlagos -- the people's circuit, the crowd right on top of the cars."),
        ("colour", "Right where he'd want to be. Fanon wrote for the wretched of the earth, the ones the grandstands were never built for -- and Interlagos is built in a working district, the crowd leaning in, no velvet rope. He'd feel the energy of this place in his chest."),
        ("pbp", "Decisive as ever, too."),
        ("colour", "Always. He doesn't wait for the gap to be offered, here least of all. A circuit full of people who were told to know their place, and a driver whose entire life was telling people not to. He tends to go well here, and I don't think it's coincidence."),
    ], about=("Frantz Fanon",), track="Interlagos", topic="fanon at interlagos"),

    discussion([
        ("pbp", "Goldman at Monza, then -- joy at the Temple of Speed."),
        ("colour", "Perfect match. Fastest place they race, the tifosi making an absolute glorious racket -- and Goldman's whole creed was that liberation should FEEL like something. If she can't dance, it's not her revolution; well, Monza's basically a dance at three hundred kilometres an hour."),
        ("pbp", "She'll enjoy it more than most."),
        ("colour", "She'll enjoy it more than the rest of the grid combined. Half of them treat winning as a grim duty. Goldman treats the slipstream down the back straight as a party she was personally invited to. Refreshing, honestly."),
    ], about=("Emma Goldman",), track="Monza", topic="goldman at monza"),

    # === Phill carries the erudition: he lands the fact, corrects the record, teaches
    #     the theory, and asks Benny only for the racecraft. Both men know their history. ===
    discussion([
        ("pbp", "And before you say it, Benny -- it wasn't a barrel. Everyone says barrel. Diogenes lived in a pithos, a great clay storage jar. They didn't HAVE barrels in ancient Greece."),
        ("colour", "...you're quite right, and I hate that you're right. Go on, then, finish the set."),
        ("pbp", "Threw away his only cup when he saw a boy drink from cupped hands. Told Alexander the Great, who'd offered him anything he liked, to kindly stop blocking the sun."),
        ("colour", "And THAT'S the man in car nineteen, who'll cheerfully wave the leader through if he decides trophies are a delusion. Half the time it's not slowness, Phill. It's a lifestyle."),
    ], about=("Diogenes",), topic="diogenes the jar"),

    discussion([
        ("pbp", "People hear 'Machiavellian' and picture a villain. But the man wrote a whole second book, the Discourses, that's a love letter to the Roman REPUBLIC. He was a republican, Benny."),
        ("colour", "He was. The Prince reads more like a job application -- written after the Medici tortured him and threw him out, basically saying 'look how useful I'd be, please employ me.'"),
        ("pbp", "So is he the cynic everyone thinks, or the idealist who got a bad press?"),
        ("colour", "Bit of both, which is why he's lethal in the car. He'll do the ruthless thing AND believe it serves a higher cause. Most dangerous man on the grid: the one with a clear conscience and a late dive."),
    ], about=("Niccolò Machiavelli",), topic="machiavelli the republican"),

    discussion([
        ("pbp", "Here's a thread the casual viewer misses: Césaire taught Fanon. Literally. Schoolteacher in Martinique, Fanon in the classroom -- and Césaire helped invent Négritude before Fanon wrote a word."),
        ("colour", "Which is why when those two race together it's not a rivalry, it's a relay. The teacher hands the baton to the student, and the student goes further and angrier than the teacher ever did."),
        ("pbp", "You can see the lineage in the driving."),
        ("colour", "Same root, two flowers. Césaire's the poetry, Fanon's the fight. And neither of them, you'll notice, has ever once waited to be told they're allowed past."),
    ], about=("Aimé Césaire", "Frantz Fanon"), topic="cesaire taught fanon"),

    discussion([
        ("pbp", "Spare a thought for Paine. Wrote the pamphlet that lit the American Revolution, then the one that rattled Britain -- and ALSO, decades early, sketched out what's basically a citizen's pension in Agrarian Justice. Visionary."),
        ("colour", "And died with about six people at his funeral. Annoyed too many of the right people. There's a lesson in that for a man running sixth and telling everyone the truth on the radio."),
        ("pbp", "Right too soon is still wrong, as far as the world's concerned."),
        ("colour", "Story of his life and most of his races. He'll make the brave honest call three laps before it's fashionable, and get nothing for it but a place in the history books. Cold comfort at the flag."),
    ], about=("Thomas Paine",), topic="paine agrarian justice"),

    discussion([
        ("pbp", "And a bit of literary history the textbooks skip, Benny: Wollstonecraft was Mary Shelley's mother. Wrote the Vindication, then died days after giving birth to the woman who'd write Frankenstein."),
        ("colour", "So one generation argues for the rights of woman, and the next invents science fiction warning what happens when you build something and refuse to care for it. There's a family motto in there somewhere."),
        ("pbp", "Reason and consequences, handed down."),
        ("colour", "And it shows. She races like someone who's read the ending -- measured, fearless, no theatrics. The grown-up in a field of toddlers with PhDs."),
    ], about=("Mary Wollstonecraft",), topic="wollstonecraft and shelley"),

    discussion([
        ("pbp", "Let me set this one up properly for the listener, because it's Foucault's big idea. The panopticon -- Bentham's prison design: one tower, every cell visible, but you can never tell if you're being watched. So you behave as if you always are. Foucault said that's modern power in one building."),
        ("colour", "Spot on. You don't need a guard for every cell, just the POSSIBILITY of a guard."),
        ("pbp", "So translate it to the track for me -- where's the panopticon out here?"),
        ("colour", "The telemetry, Phill. Every input logged, every lift, every lazy apex on a screen on the pit wall. Nobody's shouting at them -- but they all drive like someone's watching, because someone always could be. Foucault would call this the most honest racetrack ever built."),
    ], about=("Michel Foucault",), topic="the panopticon"),

    discussion([
        ("pbp", "And I want to correct the record while he's on screen. That book everyone quotes, The Will to Power? Nietzsche never finished it. His sister cobbled it together from his notebooks after he collapsed -- and she was a raging antisemite who bent his name toward people he'd have despised."),
        ("colour", "Genuinely important, that. He broke with the antisemites in his own lifetime, in writing. The monster version of Nietzsche is largely his sister's edit."),
        ("pbp", "So the man and the myth aren't the same driver."),
        ("colour", "Rarely are. Read him straight and he's wilder and stranger and a lot less use to tyrants than they wanted. On track? Fearless, contradictory, occasionally magnificent, occasionally in a hedge. Like the actual books."),
    ], about=("Friedrich Nietzsche",), topic="nietzsche's sister"),

    discussion([
        ("pbp", "Now I have to defend Adorno's record on one thing, Benny, and you'll laugh: the man HATED jazz. Wrote furious essays about it. Genuinely thought it was a con."),
        ("colour", "He did, and it's the worst take in the entire Frankfurt School, which is a competitive field. Bloke who could x-ray a whole civilisation, completely bounced off a saxophone."),
        ("pbp", "Even the giants have a blind spot."),
        ("colour", "Every one of them. Same Adorno who'll read this race like a sacred text will utterly fail to enjoy a single second of it. Misses the music, Phill. Brilliant man, no rhythm."),
    ], about=("Theodor Adorno",), topic="adorno hated jazz"),

    discussion([
        ("pbp", "Plato's whole worldview's in one image, and I think it actually helps watching this. The cave: people chained facing a wall, mistaking shadows for the real thing. One gets out, sees the sun, comes back -- and they think HE'S the mad one."),
        ("colour", "And every driver on this grid is convinced HE'S the one who got out of the cave and everyone else is watching shadows."),
        ("pbp", "All twenty of them. Can't all be right."),
        ("colour", "Can't all be right, all certain they are. That's the whole sport, that's the whole of philosophy, and that's why the gravel stays so busy. Reality's the bloke who came back from the sun. The wall's where they keep ending up."),
    ], about=("Plato",), topic="the cave"),

    discussion([
        ("pbp", "Marx on the grid, and people forget how skint he was. Exiled to London, broke for years, writing Capital in the British Museum reading room while the rent went unpaid. Buried up in Highgate under that enormous head."),
        ("colour", "The great theorist of capital, who could never get any. There's something almost tender in it -- the man saw the whole machine clearly precisely because it kept grinding HIM."),
        ("pbp", "Clear sight from the cheap seats."),
        ("colour", "Best view in the house, the cheap seats. He drives like a man who's read the whole system's accounts and knows exactly who's getting paid -- and it's never him. Patient, relentless, faintly furious. Watch him in the long runs."),
    ], about=("Karl Marx",), topic="marx in london"),

    # === The stewards as philosophy: justice, punishment, and who the rules fall on ===
    discussion([
        ("pbp", "A penalty just came down, and I can't not say it: Foucault literally wrote the book on this. Discipline and Punish -- punishment shifting from the scaffold to the quiet, constant correction of behaviour."),
        ("colour", "And the stewards are his case study come to life. They don't need to punish everyone -- they need everyone to drive as if they MIGHT. The five-second penalty isn't really about the five seconds."),
        ("pbp", "It's about the watching."),
        ("colour", "It's about the watching. Twenty of the most rebellious minds in history, all lifting a fraction early at the white line because a camera might be looking. Foucault would be unbearable about how right he was."),
    ], about=("Michel Foucault",), topic="discipline and punish"),

    discussion([
        ("pbp", "Now the anarchists will have FEELINGS about a penalty, Benny. Bakunin, Goldman, Stirner -- authority handing down a verdict is the one thing they exist to reject."),
        ("colour", "To Stirner the stewards are just another spook -- a ghost with a clipboard, real only because everyone agrees to bow. Bakunin wants to overturn the whole stewards' table. Goldman wants to know who elected them."),
        ("pbp", "So do they serve it?"),
        ("colour", "They have to -- that's the joke. The barrier doesn't care about your theory of authority, and neither does the timing screen. You can reject the legitimacy of the penalty all you like, at minus five seconds, in public."),
    ], about=("Mikhail Bakunin", "Emma Goldman"), topic="anarchists and stewards"),

    discussion([
        ("pbp", "Here's the real argument under every stewards' decision, and it's an old one: was that wrong because of the RULE he broke, or because of the HARM he did?"),
        ("colour", "That's the whole split. One camp says a rule's a rule -- break it and you're guilty, outcome be damned. The other says no harm, no foul; it's the wreckage that matters, not the rulebook."),
        ("pbp", "Racing incident versus avoidable contact."),
        ("colour", "Exactly that, every single time. 'They both could've left more room' is the no-harm-no-foul crowd. 'He stuck his nose where it didn't fit' is the rule-is-a-rule crowd. The stewards are refereeing a two-thousand-year-old ethics seminar, with replays."),
    ], topic="rule or harm"),

    discussion([
        ("pbp", "Nietzsche on punishment is darker and cleverer than people expect. In the Genealogy he traces the whole idea of guilt back to DEBT -- in German it's the same word, Schuld."),
        ("colour", "It is, and it's a brilliant nasty insight. Punishment, he says, began as a creditor collecting -- you owe, you couldn't pay, so society takes it out of your hide instead. A penalty isn't justice, it's a debt being settled."),
        ("pbp", "So five seconds is the instalment plan."),
        ("colour", "Five seconds is the instalment plan, and the stewards are the collection agency. Nietzsche would watch a driver serve a penalty and see the oldest transaction there is -- pain accepted in place of what's owed. Cheerful chap."),
    ], about=("Friedrich Nietzsche",), topic="punishment and debt"),

    discussion([
        ("pbp", "Plato wouldn't see a penalty as revenge at all, would he. For him punishment is supposed to IMPROVE the wrongdoer."),
        ("colour", "That's the Gorgias line -- better to be punished than to get away with it, because escaping it leaves your soul sick. To Plato a five-second penalty is medicine, and the driver who dodges one is the one you should pity."),
        ("pbp", "Try selling that on the cooldown lap."),
        ("colour", "Try selling it to anyone, ever. 'This penalty is for the good of your soul' -- you'd be lucky to get the helmet off in one piece. But it's the most optimistic theory of the stewards' room ever written, I'll give him that."),
    ], about=("Plato",), topic="punishment as medicine"),

    discussion([
        ("pbp", "Rand's position on a penalty would be fascinating, because she actually BELIEVED in objective law -- impartial rules, applied equally."),
        ("colour", "She did. In principle she's the stewards' biggest fan -- objective, blind, no favourites. In practice, the instant a rule constrains HER, it becomes tyranny by committee and an outrage against the rational individual."),
        ("pbp", "Rules for thee."),
        ("colour", "Rules she'd have written herself, right up until they cost her a place. That's the gap between the philosophy and the cockpit -- and with Rand it's a wide one, usually measured in gravel."),
    ], about=("Ayn Rand",), topic="rand and objective law"),

    discussion([
        ("pbp", "Machiavelli wouldn't moralise about a penalty for a second -- he'd just ask whether it WORKS."),
        ("colour", "Pure instrument, to him. He wrote that a leader should punish decisively, all at once, and be done -- cruelty rationed badly only breeds contempt. He'd want the stewards FEARED, not loved, and certainly not debated."),
        ("pbp", "Better feared than loved."),
        ("colour", "His actual line, near enough. He'd look at a wishy-washy five-second penalty for taking someone out and tut -- too soft, drags on, satisfies nobody. Machiavelli's stewards hand down the drive-through and move on. Brutal, but you'd not do it twice."),
    ], about=("Niccolò Machiavelli",), topic="machiavelli on punishment"),

    discussion([
        ("pbp", "And Marx would point at the stewards and ask the awkward question: whose interests do these rules actually serve?"),
        ("colour", "Every time. To Marx the rulebook isn't neutral -- it's written by the people with the most to protect, and it tends, funnily enough, to fall hardest on the ones who didn't write it. The law as the will of whoever owns the most garages."),
        ("pbp", "Cynical."),
        ("colour", "Or clear-eyed, depending where you're standing. He's not wrong that the penalties land more on the wild outsiders than the established front-runners -- though Benny's view is that's mostly because the outsiders keep driving into people."),
    ], about=("Karl Marx",), topic="marx on the rulebook"),

    discussion([
        ("pbp", "I have to ask the daft question the whole crowd's thinking, Benny. Why FIVE seconds? Why not four, or six?"),
        ("colour", "Genuinely? Because somebody, somewhere, in a meeting, decided five FELT right. There's no law of physics in it. It's a number a committee agreed on over lukewarm coffee, and now it's the difference between a trophy and nothing."),
        ("pbp", "The cosmos shrugs."),
        ("colour", "The cosmos shrugs and the timing screen does not. That's the whole human comedy in one penalty -- an arbitrary number, applied with total seriousness, deciding everything. Douglas Adams could've retired on it."),
    ], topic="why five seconds"),

    discussion([
        ("pbp", "Last one on the stewards, and it's the Fanon and Cesaire point: it matters enormously WHO the rules tend to fall on."),
        ("colour", "It does. Both of them spent their lives on exactly that -- not whether there are rules, but who writes them, who they're enforced against, and who gets the benefit of the doubt. A penalty isn't just a penalty; it's a question about whose racing gets called 'aggressive' and whose gets called 'robust.'"),
        ("pbp", "Same move, two words for it."),
        ("colour", "Same move, two words, and which word you get can depend on which end of the grid you started. They'd watch the stewards closely -- not cynically, just carefully. It's the most serious point in the whole conversation, and worth making straight."),
    ], about=("Frantz Fanon", "Aimé Césaire"), topic="who the rules fall on"),
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


# =============================================================================
# THE COUNTDOWN TO GREEN -- the pre-race show's phrasings, as pools.
#
# The preview used to be near-fixed: the same welcome, the same hand-off, the same
# "stand by", every single race, only the names changing. These pools give every beat
# of it the fresh-pick variety the rest of the booth already has -- colour.py's
# preview() draws one line from each per race. Placeholders the booth fills:
# {circuit}, {name} (the Grand Prix), {pole}, {team}, {second}.
# =============================================================================

# Phill opens the show.
PREVIEW_WELCOME = [
    "Welcome to the Political Philosophy Racing League -- live at {circuit} for the {name}.",
    "You're here with the Political Philosophy Racing League, and a very warm welcome to {circuit} for the {name}.",
    "The Political Philosophy Racing League is about to go racing at {circuit} -- this is the {name}.",
    "Hello and welcome to the Political Philosophy Racing League, here at {circuit} for the {name}, and what a day for it.",
    "This is the Political Philosophy Racing League, live from {circuit} -- moments now from the {name}.",
    "Good afternoon, and welcome to the Political Philosophy Racing League at {circuit}, where the {name} is about to begin.",
    "Twenty of history's most dangerous minds, one grid: welcome to the Political Philosophy Racing League, live at {circuit} for the {name}.",
    "You join the Political Philosophy Racing League at {circuit} -- the {name}, and the grid is forming up.",
]

# The pole announcement -- the front row.
PREVIEW_POLE = [
    "Pole position goes to {pole} for {team}, {second} alongside on the front row.",
    "It's {pole} on pole for {team}, with {second} sharing row one.",
    "{pole} takes pole for {team} -- {second} lines up alongside.",
    "Top of the timesheet and on pole: {pole}, {team}. {second} for company on the front row.",
    "Pole, and the clean side of the grid, belongs to {pole} of {team} -- {second} next to them.",
    "{pole} has put {team} on pole, {second} doing the chasing from second.",
]

# When only one car set a time (vanishingly rare) -- no front-row partner to name.
PREVIEW_POLE_SOLO = [
    "Pole position: {pole} for {team}.",
    "{pole} on pole for {team}, and precious little company out there.",
]

# Phill throws to Benny for the watch-points.
PREVIEW_HANDOFF = [
    "So what are we watching for, Benny?",
    "Benny -- where's this one won and lost?",
    "Talk us through it, Benny. What matters today?",
    "What's the watch-word, Benny?",
    "Set the table for us, Benny -- what should we keep our eyes on?",
    "So what wins it round here, Benny?",
    "Where should we be looking when the lights go out, Benny?",
]

# Phill brings the grid to the boil. "Stand by" stays the ritual signal-word.
PREVIEW_STANDBY = [
    "Lights out is moments away. Stand by.",
    "We are moments from lights out. Stand by.",
    "Not long now -- they're forming up on the grid. Stand by for lights.",
    "The pit lane is closed, the grid is set. Stand by.",
    "Here we go, then -- the formation lap is done. Stand by for the start.",
    "Visors down, revs up. Stand by for lights out.",
    "This is it. Twenty cars, one green light to come. Stand by.",
]

# --- the shows as conversations (give-and-take for the pre- and post-race programmes) --
# Benny reacts to arriving at the circuit -- an occasional warm word after Phill's
# welcome, so the show OPENS as two people, not one voice reading a card.
PREVIEW_WELCOME_REACT = [
    "Love this place. Always delivers.",
    "Big one, this. Can't wait to get going.",
    "Cracking venue to be at -- let's have a race.",
    "Good to be here, Phill. The paddock's buzzing.",
    "One of the great days out, this.",
    "Right then. Let's see what they've brought.",
    "Been looking forward to this one all week.",
]

# Phill's short response after Benny's read on the pole-sitter -- factual, agreeing, in
# HIS register; he never adds a verdict of his own, he just takes the ball back.
PHILL_POLE_RESPONSE = [
    "Strong place to start, then.",
    "A marker laid down, no question.",
    "We'll see if it holds when the lights go out.",
    "The front row's settled, then.",
    "Noted -- and we'll be watching that closely.",
    "Best seat in the house, as you say.",
    "Pole's one thing. Sunday's another.",
]

# The booth reacts to a podium answer -- Benny with a verdict in his register, Phill with
# a flat reportorial nod -- so the drivers are talked WITH, not just recorded. Each is a
# (role, line) turn, so the reaction can come from either man. Generic enough to follow
# any answer.
BOOTH_PODIUM_REACT = [
    ("colour", "For my money, that's the line of the day."),
    ("colour", "Well said, that. Hard to argue with a word of it."),
    ("colour", "See, that's why they won -- clear in the head, even now."),
    ("pbp", "Strong words from the podium."),
    ("colour", "I'll tell you what, they mean every syllable."),
    ("pbp", "And there's the verdict, straight from the cockpit."),
    ("colour", "Now THAT is a racing driver talking."),
    ("pbp", "Nicely put, that."),
    ("colour", "Mind you, you'd talk a good game too, having just won."),
]

# Benny's read on the pole-sitter, bucketed by their stat line. _pole_read() picks the
# bucket from the numbers, then a phrasing from the pool. {name} is the pole-sitter.
POLE_READ = {
    "quick_no_head": [
        "Quick as anything over one lap, {name} -- but the head for a race? We'll see. Could come back to bite.",
        "Sensational on a single lap, {name}. Whether the patience is there for a whole race is another matter entirely.",
        "{name} found half a second from nowhere in qualifying. Now we learn if they can do it for a full afternoon without binning it.",
    ],
    "racer": [
        "And {name} can race as well as qualify -- long afternoon for the rest, this.",
        "{name} on pole, and this one races every bit as well as they qualify. The rest are in trouble.",
        "Worst possible news for the field: {name} starts first and is a proper racer with it.",
    ],
    "tyre": [
        "{name} on pole AND gentle on the tyres -- track position and tyre life? That's the dream.",
        "{name} out front and famously kind to the rubber -- that's the combination everyone fears.",
        "Pole for {name}, and they look after a set of tyres better than anyone. Ominous.",
    ],
    "plain": [
        "{name} starts where everyone wants to be. Now they have to keep it.",
        "{name} on pole. The hard part starts when the lights go out.",
        "Best seat in the house for {name}. Holding it is another thing entirely.",
        "{name} has done the first job perfectly. The rest of the afternoon to do the rest.",
    ],
}

# What-to-watch phrasings, by what the circuit's own numbers say. _track_tips() reads
# the buckets off the track and picks a phrasing for each, so the same circuit never
# reads its watch-points the same way twice.
TRACK_TIP_OPENER = ["Well -- ", "Right -- ", "Where do I start... ", "Plenty, as ever -- ", "Lots to like -- "]

TRACK_TIP_PASS = {
    "hard": [
        "passing here is brutal, so track position off the line is everything -- get the start wrong and your Sunday's done",
        "you cannot pass round here for love nor money, so qualifying and the getaway are the whole game",
        "overtaking is a nightmare on this circuit -- whoever leads into turn one has a real head start on the afternoon",
    ],
    "easy": [
        "they'll be streaming past all afternoon down these straights -- slipstream city",
        "this place serves up passing for fun -- expect places to change hands lap after lap",
        "with these straights nobody is safe -- a lead here is written in pencil",
    ],
    "fair": [
        "a fair test for overtaking -- you can make a move stick if you're brave",
        "passing is on, but you'll have to earn it -- this rewards a clean, committed move",
        "it's there to be done if you're brave and patient -- no gifts, but no fortress either",
    ],
}

TRACK_TIP_TYRE = {
    "high": [
        "and the tyres take an absolute hammering -- this is a strategist's race",
        "and these tyres won't last -- whoever's kindest to the rubber writes the result",
        "and tyre wear is savage here, so the stops, and the timing of them, decide it",
    ],
    "low": [
        "and the tyres last forever, so expect them flat out from lights to flag",
        "and there's barely any wear, so it's a straight fight on pace, not on saving rubber",
        "and the rubber holds up all day -- nobody's nursing anything, it's pure speed",
    ],
}

# THE RUNNING GAG -- writing off the Objectivism car before a wheel has turned.
# Rand and Stirner are contractually doomed (drivers.py gives them racecraft 0.0 and a
# guaranteed early retirement), and the booth has FEELINGS about it. One of these plays
# every Countdown to Green: the same beloved joke, never the same words twice. Each item
# is a list of (role, line) turns -- some a dry one-liner, some a quick exchange.
OBJECTIVISM_PREVIEW = [
    [("colour", "And before a wheel turns, let me save you the suspense: the Objectivism car will not finish. It never does. Rand and Stirner, two laps of heroic self-reliance and a long, principled walk back to the paddock.")],

    [("pbp", "Any word from the Objectivism garage, Benny?"),
     ("colour", "They've refused the strategy, the tyre data, and, I gather, the concept of other cars. Rand thinks cooperation is a sin; Stirner thinks the pit board is a ghost. Out by lap two, the pair of them.")],

    [("colour", "Keep half an eye on the Objectivism pit, purely for the comedy. Rand built an entire philosophy on the heroic individual who needs no one -- and it has never once got her past half-distance. Turns out the universe is a collective effort.")],

    [("pbp", "Optimistic for Rand this weekend?"),
     ("colour", "Optimistic she'll reach the first corner. After that it's her against physics and her own principles, and physics has a perfect record.")],

    [("colour", "The Objectivism car: the one team on this grid that holds the rulebook to be tyranny and the marshals to be a mob. Rand and Stirner. They will not finish, and they will be insufferable about it.")],

    [("colour", "Rand's whole creed is that you owe nobody anything -- not the team, not the tow, not the people who built the engine. Lovely theory. Falls apart the instant you need a pit crew, which is every single lap.")],

    [("pbp", "And the Objectivism pairing?"),
     ("colour", "A masterclass in not finishing, same as ever. Rand thinks asking for help is weakness, Stirner thinks help is a spook, and between them they've the racecraft of a deckchair.")],

    [("colour", "I'll tell you now so you can enjoy the rest in peace: the Objectivism car is going home early. There's a lovely irony in a philosophy of triumph that has never, not once, crossed a finish line -- and I intend to savour it for the full distance.")],

    [("colour", "Rand wrote a thousand pages on the virtue of the winner who owes nobody a thing. Has yet to see a chequered flag. There's your seminar, free of charge.")],

    [("pbp", "Anything from the Objectivists before we go racing?"),
     ("colour", "Defiant. Magnificently, pointlessly defiant. They'll wave off every instruction on principle and retire bang on schedule, and afterwards Rand will explain that the gravel trap was collectivism's fault.")],

    [("colour", "And as ever, form no attachment to the Objectivism car. Rand and Stirner: two great theorists of standing alone, doing precisely that -- off the track, by lap three.")],

    [("colour", "The Objectivism garage radiating confidence, which on current form means absolutely nothing. Rand cannot account for the one fact that settles her every Sunday -- you do not win a race entirely by yourself -- and she'd sooner retire than admit it. So she does.")],

    [("pbp", "Rand starts down the order again. Surprised?"),
     ("colour", "Nothing about Rand surprises me any more. She'll call the grid a conspiracy of the mediocre, refuse a single tow on principle, and be in the wall by Sunday lunch. It's almost reassuring.")],

    [("colour", "Spare a thought, in advance, for the Objectivism crew -- the only pit wall on the grid whose driver treats a pit call as an assault on her liberty. They've half stopped putting the boards out. Why bother? She'd only resent the help.")],
]


# A name to watch from outside the top five -- a buried strategist who'll climb, or a
# charger who won't sit still. _watch_name() picks the bucket; phrasing from the pool.
# {name} is the driver, {start_ord} their spelled grid position.
WATCH_STRATEGIST = [
    "And keep an eye on {name}, starting {start_ord} -- best strategic mind on this grid. Don't be surprised to see them carve through.",
    "Don't lose sight of {name} down in {start_ord}. Sharpest tactical head out there -- this is exactly the sort to come good on strategy.",
    "{name} only {start_ord}? Won't matter. Cleverest racer on the grid -- they'll make the undercut sing and you'll see them near the front by the end.",
    "Watch for {name} from {start_ord}. Buried, yes, but nobody reads a race better -- give it a stint or two and they'll have climbed.",
]
WATCH_CHARGER = [
    "{name} down in {start_ord} won't last long there -- that one does not believe in holding position.",
    "{name} starts {start_ord}, which won't suit them at all -- pure racer, allergic to sitting in a queue. Elbows out from the off.",
    "Keep your eye on {name} in {start_ord}. They'll be scything forward inside a handful of laps -- staying put isn't in their nature.",
    "{name} from {start_ord} is my pick for fireworks -- that's a driver who treats every car ahead as a personal insult.",
]

# THE POLE-SITTER, IN CHARACTER. The front of the grid is the show's centrepiece, so
# the pole read isn't a stat bucket -- it's a read on WHO this is. Benny says what it
# MEANS that this particular philosopher is starting first, the politics carried by the
# fact of the pole. _pole_read() uses this when the pole-sitter has a line, and falls
# back to the stat-bucket POLE_READ for anyone who doesn't. {name} available but rarely
# needed (the line already names them).
POLE_CHARACTER = {
    "Plato": [
        "Plato on pole -- of course. He'd tell you the perfect race already exists, complete, in a higher realm; today he simply drives its shadow. Frightening when he's this far up.",
        "Plato leads them off, and he'll have seen this whole race in his head before the lights. The rest are chasing a copy of a lap he's already perfected.",
    ],
    "Diogenes": [
        "Diogenes on pole? Threw away everything he owned and most of the rulebook, and somehow he's quickest. There's a lesson in that, if you can stand the barrel.",
        "Pole for the Cynic -- no plan, no theory, no respect for any of it, and first on the grid regardless. He'd find that very funny.",
    ],
    "Karl Marx": [
        "Marx on pole, and he'll tell you it was inevitable -- the right preparation, the long game, history arriving bang on schedule. Annoyingly, from there, he's usually right.",
        "Marx leads, and don't expect heroics from him -- he believes the race is decided by the deep conditions, not the dramatics. He's just made sure the conditions favour him.",
    ],
    "Rosa Luxemburg": [
        "Luxemburg on pole, and she didn't get there by anyone's master plan -- pure instinct over one lap. Whether she can hold that nerve for a whole race is the question.",
        "Pole for Luxemburg, who trusts the moment over the plan every time. One brilliant lap proves the point. A full race will test it.",
    ],
    "Mikhail Bakunin": [
        "Bakunin on pole -- all-out attack over one lap, no thought for what comes after. Thrilling. Now we find out if there's a race plan underneath all that fury. Spoiler: there isn't.",
        "Pole for Bakunin, the man who says the urge to destroy is a creative one. He's just destroyed the qualifying order. The race is another matter.",
    ],
    "Emma Goldman": [
        "Goldman on pole, and you can tell she loved doing it -- if the lap's no joy, it's not worth setting, far as she's concerned. She enjoyed that one.",
        "Pole for Goldman, who'd dance her way round if they let her. Freedom and a good time, at speed -- that's the whole programme.",
    ],
    "Friedrich Nietzsche": [
        "Nietzsche on pole, which is exactly where he believes he belongs, and several places higher than that. Will to power over one lap -- now he has a whole field to overcome, as well as himself.",
        "Pole for Nietzsche. He'll have driven that lap as though he'd have to drive it again forever -- and that, terrifyingly, tends to be quick.",
    ],
    "Simone de Beauvoir": [
        "de Beauvoir on pole -- and she'd remind you nobody is BORN on pole. She built that lap, choice by choice, and she'll defend it exactly the same way.",
        "Pole for de Beauvoir: rigorous, deliberate, nothing left to chance. One is not born quickest, she'd say -- one becomes it. She has.",
    ],
    "Niccolò Machiavelli": [
        "Machiavelli on pole, and don't mistake it for pace -- it was planning. He decided he'd start here on Thursday, and here he is.",
        "Pole for the great strategist. Cunning, not speed, put him there, and cunning is a lot harder to take off a man over a race.",
    ],
    "Theodor Adorno": [
        "Adorno on pole, looking thoroughly miserable about it. He'll tell you the whole spectacle is a con -- then go and top it anyway. Bleak. Quick, though.",
        "Pole for Adorno, who thinks the entire show is bread and circuits, and has just won the most important lap of it. The contradiction will keep him up tonight.",
    ],
    "Herbert Marcuse": [
        "Marcuse on pole -- got there by refusing to lift where everyone else did. The Great Refusal, one lap of it. Now he has to keep refusing for a whole afternoon.",
        "Pole for Marcuse, the man who says no to the corner the rest accept. He said no all the way round, and it was quickest.",
    ],
    "Michel Foucault": [
        "Foucault on pole, having found a lap nobody else could see -- he spends his life taking the line the track tells you not to. Today it put him first.",
        "Pole for Foucault. The circuit disciplines everyone onto the obvious line; he took the one it was built to keep him off, and beat the lot of them.",
    ],
    "Jacques Derrida": [
        "Derrida on pole, which even he would call an unstable position containing the seeds of its own undoing. Lovely lap, mind. Don't ask him to explain it.",
        "Pole for Derrida -- he found the gap in everyone's certainty about the quickest line, and drove through it. Whether he can do it twice, nobody knows, least of all him.",
    ],
    "Frantz Fanon": [
        "Fanon on pole -- took it, didn't wait to be given it. That's the man entire, in one lap.",
        "Pole for Fanon, decisive as ever. You seize your place out here, he'd say; nobody hands it over. He's seized the best one going.",
    ],
    "Aimé Césaire": [
        "Césaire on pole, the composed one -- no fireworks, just a lap written out longhand and quicker than everyone else's shouting.",
        "Pole for Césaire: measured, dignified, not a wheel out of place. He let the hotheads tear themselves up and quietly went fastest.",
    ],
    "Richard Rorty": [
        "Rorty on pole, and he won't claim it's the 'truly' perfect lap -- just the one that worked. Worked better than everyone's, mind.",
        "Pole for Rorty, who stopped asking whether his line was correct and simply drove the one that kept paying off. It paid off all the way to first.",
    ],
    "Mary Wollstonecraft": [
        "Wollstonecraft on pole -- out-thought the braking zones rather than out-muscled them. Reason, applied at speed, and quicker than the muscle.",
        "Pole for Wollstonecraft: clear-headed, principled, no theatrics. She reasoned her way to the front while the others were still arguing.",
    ],
    "Thomas Paine": [
        "Paine on pole, plain and honest -- no tricks, just a quick, clean lap anyone could see coming. Common sense, at two hundred miles an hour.",
        "Pole for Paine. No cunning to it, no theatre -- plain courage, plainly applied, and it was enough to top the lot.",
    ],
    "Ayn Rand": [
        "Rand on pole? Savour it, folks -- it is the undisputed high point of her weekend, and her weekend ends at roughly lap two.",
        "Pole for Rand, won entirely alone, with no tow and no help, exactly as she'd insist. Holding it will require other cars to exist, which is where it all falls down for her.",
    ],
    "Max Stirner": [
        "Stirner on pole, owing the achievement to no one and acknowledging the same. He'd call the grid a phantom and the rules a ghost -- right up until a very solid gravel trap on lap two.",
        "Pole for Stirner, who recognises no authority, including the one that just timed him fastest. Enjoy it while it lasts. It won't.",
    ],
}

# THE GRID'S OWN STORYLINES -- the heart of the revamped Countdown. Given the
# qualifying order, the booth previews a real RIVALRY about to renew itself: who's
# lining up where, and the grudge or the kinship behind it. Keyed by the pair (order
# doesn't matter -- the detector works out who's ahead). Placeholders: {ahead} and
# {behind} (the names, by grid position), {ahead_ord} and {behind_ord} (their spelled
# grid slots). The HOOK names the thinkers directly, so it reads right whoever's in
# front. _grid_storylines() scores pairs by how high and how close they start.
PREVIEW_MATCHUP = {
    frozenset(("Karl Marx", "Mikhail Bakunin")): [
        banter([("pbp", "{ahead} starts {ahead_ord}, {behind} right there in {behind_ord} -- and there's history between those two."),
                ("colour", "History? They split the entire workers' movement in half. Marx had Bakunin thrown out of the International; Bakunin called him a tyrant-in-waiting. A century and a half later, here they are, a grid slot apart. This will not stay civil.")]),
        banter([("pbp", "Marx and Bakunin, {ahead_ord} and {behind_ord}."),
                ("colour", "The great schism, lining up to do it all again. One wants the disciplined plan, the other wants to tear the plan up. They could never share a committee -- let's see if they can share a corner.")]),
    ],
    frozenset(("Michel Foucault", "Jacques Derrida")): [
        banter([("pbp", "{ahead} ahead of {behind} on the grid -- {ahead_ord} to {behind_ord}."),
                ("colour", "These two fell out for years, and over a book, would you believe -- Foucault and Derrida, the great post-structuralist falling-out. Starting this close, that old argument's about to get a rematch at speed.")]),
    ],
    frozenset(("Frantz Fanon", "Aimé Césaire")): [
        banter([("pbp", "{ahead} lines up {ahead_ord}, {behind} {behind_ord} -- teacher and student, these two."),
                ("colour", "Césaire taught Fanon damn near everything he knows. The one thing he forgot to teach him was to let the old man back through. Watch this one -- there's real love in it, and absolutely no quarter.")]),
    ],
    frozenset(("Thomas Paine", "Mary Wollstonecraft")): [
        banter([("pbp", "{ahead} and {behind}, {ahead_ord} and {behind_ord}."),
                ("colour", "Rights of Man and Rights of Woman, side by side on the grid. Same revolution, different pamphlet -- and they'll race each other as equals, which is exactly how both of them would insist on it.")]),
    ],
    frozenset(("Karl Marx", "Ayn Rand")): [
        banter([("pbp", "{ahead} ahead of {behind} -- {ahead_ord} and {behind_ord}."),
                ("colour", "The whole twentieth century in two cars. Marx the collective, Rand the lone individual, and neither would lift to save their life. Mind you, only one of them will still be running by lap three, and it isn't the one who refuses a tow.")]),
    ],
    frozenset(("Simone de Beauvoir", "Mary Wollstonecraft")): [
        banter([("pbp", "{ahead} starts {ahead_ord}, {behind} {behind_ord}."),
                ("colour", "Two centuries apart, the very same fight -- the rights and the freedom of women, argued first by Wollstonecraft and taken up by de Beauvoir. Starting together today. The younger argument has the legs, but don't count out the original.")]),
    ],
    frozenset(("Friedrich Nietzsche", "Plato")): [
        banter([("pbp", "{ahead} and {behind} -- {ahead_ord} to {behind_ord} on the grid."),
                ("colour", "Nietzsche spent his whole career calling Plato's perfect world a fairy story. Now they line up in the real one, a few feet apart. He'd love nothing more than to bin the old idealist at the first corner.")]),
    ],
    frozenset(("Plato", "Diogenes")): [
        banter([("pbp", "{ahead} and {behind}, {ahead_ord} and {behind_ord}."),
                ("colour", "Oh, these two. Diogenes once plucked a chicken, held it up and shouted 'behold, Plato's man' -- just to make the great philosopher look a fool. That contempt has lasted two thousand years, and it's lining up on a grid today.")]),
    ],
    frozenset(("Theodor Adorno", "Herbert Marcuse")): [
        banter([("pbp", "{ahead} ahead of {behind} -- {ahead_ord} and {behind_ord}."),
                ("colour", "The Frankfurt split, right there. When the students rose up, Marcuse went to the barricades and Adorno rang the police. One takes the corner, the other analyses it. Starting this close, we'll see which wins.")]),
    ],
    frozenset(("Niccolò Machiavelli", "Plato")): [
        banter([("pbp", "{ahead} and {behind} on the grid, {ahead_ord} to {behind_ord}."),
                ("colour", "The realist and the dreamer. Plato wants the ideal city; Machiavelli wants to know how power actually works on a wet Tuesday. The Prince never did have time for the Republic -- and he'll have even less for it into Turn 1.")]),
    ],
    frozenset(("Rosa Luxemburg", "Karl Marx")): [
        banter([("pbp", "Teammates {ahead} and {behind}, {ahead_ord} and {behind_ord} -- and not exactly in lockstep."),
                ("colour", "Same team, same cause, endless argument. Marx trusts the long-laid plan; Luxemburg trusts the moment and won't wait to be told. She'd seize a gap he'd let develop for ten laps. No team orders are going to settle THAT.")]),
    ],
    frozenset(("Emma Goldman", "Mikhail Bakunin")): [
        banter([("pbp", "{ahead} and {behind}, teammates, {ahead_ord} and {behind_ord}."),
                ("colour", "Two anarchists on the same team, which means absolutely no orders and no holding station -- they'd both be insulted to be asked. No gods, no masters, and apparently no exceptions for each other. Flat out, the pair of them.")]),
    ],
    frozenset(("Simone de Beauvoir", "Friedrich Nietzsche")): [
        banter([("pbp", "{ahead} ahead of teammate {behind} -- {ahead_ord} to {behind_ord}."),
                ("colour", "There's a lineage here. de Beauvoir took Nietzsche's idea that you make yourself out of nothing handed down. But she never forgot the grid you start from, the car you're given -- the bit he sails straight past. Same garage, opposite blind spots.")]),
    ],
    frozenset(("Jacques Derrida", "Plato")): [
        banter([("pbp", "{ahead} and {behind}, {ahead_ord} and {behind_ord}."),
                ("colour", "Derrida built a whole career taking Plato's certainties apart, line by line. Now there's a literal line between them on the grid. If anyone can find the crack in the old man's perfect lap and slip through it, it's him.")]),
    ],
    frozenset(("Niccolò Machiavelli", "Richard Rorty")): [
        banter([("pbp", "Teammates {ahead} and {behind} -- {ahead_ord} and {behind_ord}."),
                ("colour", "Two men who long ago stopped asking what the 'true' racing line is and started asking only what works. The realist and the pragmatist, same garage. No grand theory between them -- just whoever's plan pays off first.")]),
    ],
}

# THE WEATHER OUTLOOK -- a forecast beat, driven by the track's rain_chance. Real
# booths flag the sky when it matters and skip it when it doesn't; so does this.
PREVIEW_WEATHER = {
    "likely": [
        "And keep half an eye on that sky -- rain's a real threat here, and if it comes, everything you think you know about this race goes out the window.",
        "The clouds are doing the talking today. A shower is very much on the cards, and wet weather is the great leveller -- the clever ones will be watching the radar, not the timing screen.",
        "It could rain, and at this place it often does. If it turns, the strategists and the brave both get their moment -- and the order we've got could mean nothing at all.",
    ],
    "possible": [
        "There's a chance of a shower later -- not a certainty, but enough that the smart money keeps the wets within reach.",
        "Eye on the weather: it might just spit later on. Probably nothing. But 'probably' has cost people a race before now.",
    ],
    "dry": [
        "Sky's clear, track's dry, no excuses from the heavens today -- this one will be settled on pure racing.",
        "No help from the weather today -- it's dry and it'll stay dry, so whatever happens out there, they've only themselves to blame.",
    ],
}

# A KEY-CORNER callout -- name the place the race tends to be decided, drawn from the
# circuit's own overtaking corners. {corner} is supplied by _seg_scene().
PREVIEW_CORNER = [
    "Keep your eyes on {corner} -- that's where this one gets won and lost, every year.",
    "If a move's going to stick today, it'll be at {corner}. Watch that braking zone.",
    "{corner} is the place to watch -- get it right and the race opens up; get it wrong and you're a passenger.",
    "All the big moments here happen at {corner}. That's where the brave make their afternoon.",
]


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
        "{gained} places made up -- was there a particular move that broke it open?",
        "You were a man on a mission from lights out -- when did you sense the podium was on?",
        "Starting {start_ord}, most would settle for points. When did you decide to gamble for more?",
    ],
    "teammate": [
        "You and {mate} had quite the battle out there -- how close did that get?",
        "It looked like you and {mate} were really racing each other hard today?",
        "That scrap with {mate} -- was it as tense in the car as it looked from here?",
        "You gave {mate} no quarter today -- is that how it has to be between teammates?",
        "Wheel to wheel with {mate} for laps on end -- did either of you ever lift?",
        "The garage must have been holding its breath watching you and {mate}. Worth it?",
    ],
    "team_orders": [
        "Were team orders ever a consideration, or were you both free to race?",
        "Did the pit wall ever ask you to hold position, or was it gloves off?",
        "Was there ever a call to settle it between you, or were you let race?",
        "Did a voice in your ear ever tell you to back out of it?",
        "Some teams would have frozen that. Were you ever told to?",
        "No 'hold station' from the wall, then -- or did you just not fancy listening?",
    ],
    "weather": [
        "When the rain came, what was the call on the tyres?",
        "The conditions were all over the place -- how did you read them?",
        "That gamble when the weather turned -- talk us through the thinking.",
        "Everyone blinked when the sky opened. What made you commit when you did?",
        "Half the field got the tyre call wrong today. How did you get it right?",
        "Treacherous out there at the worst of it -- how much was guesswork, how much feel?",
    ],
    "survival": [
        "You took a knock out there and still brought it home -- how was the car after?",
        "There was contact early on -- how close did you come to not finishing?",
        "You carried damage to the flag -- how much was that hurting you out there?",
        "After that contact, did you ever think the podium was gone?",
        "A wounded car and a long way to go -- how did you manage it home?",
        "Most cars don't recover from a hit like that. How did yours?",
    ],
    "pole_to_win": [
        "Pole to flag, never headed -- was it as controlled as it looked from here?",
        "You led every lap -- was it ever as comfortable as the gap suggested?",
        "Lights to flag out front -- where was this race actually won?",
        "Never put a wheel wrong all afternoon -- is that harder than fighting through?",
        "From the front the whole way -- was the pressure ever really off?",
        "A lights-to-flag win can look easy. What were we not seeing from here?",
    ],
    "win_open": [
        "Take us through it -- when did you know the win was on?",
        "A brilliant drive -- where do you reckon you won this one?",
        "When did you start to believe today was your day?",
        "What was the moment it turned in your favour?",
        "Walk us through the win -- where did it come together for you?",
        "Was there a point out there where you knew nobody was catching you?",
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
        "You don't think about the whole climb. You think about the car in front, and then the next one.",
        "Starting back there frees you up, oddly. Nothing to lose, so you commit to every gap.",
        "The pace was always in the car. It was just a question of getting it through the traffic in one piece.",
    ],
    "teammate": [
        "Hard but fair. We've earned the right to race each other, and we did -- cleanly.",
        "Close. Closer than the team would have liked, I should think. But that's racing.",
        "We pushed each other all afternoon. That's what a good pairing is for -- nobody got a free ride.",
        "We respect each other enough to race hard and not put each other in the wall. That's the deal.",
        "Neither of us was going to lift, and neither of us did. I'd not have it any other way.",
        "You race your teammate hardest of all -- they've got the same machine, so there are no excuses.",
    ],
    "team_orders": [
        "We were free to race. It's the only way I'd want it.",
        "No orders. We sorted it on the track, the way it should be.",
        "If there was a call to hold station, I'd like to think I heard it... eventually.",
        "Gloves off, start to finish. The team trusts us to bring them both home, and we did.",
        "Nobody told me to move over, and I wasn't going to ask the question.",
        "The pit wall let us get on with it. To their credit, they held their nerve.",
    ],
    "weather": [
        "You commit to a read and you live with it. Today the read was right.",
        "Half of it is nerve. You can't wait to be certain -- by then you've lost it. I went early, it paid.",
        "The track tells you, if you're listening. I listened a fraction sooner than the rest.",
        "You feel the grip going through your hands before you see it. I trusted that, and dived in.",
        "Conditions like that, the brave call and the stupid call look identical until the next corner.",
        "I'd rather be a lap early on the right tyre than a lap late on the wrong one. Today that was the difference.",
    ],
    "survival": [
        "She was bruised, but she answered. You drive around the damage and hope it holds. It held.",
        "Wounded but willing. You shorten the braking, you nurse it, you count the laps down.",
        "Not pretty after that knock. But a damaged car on the podium beats a perfect one in the gravel.",
        "You learn what the car will still give you, and you ask for exactly that and no more.",
        "Every lap after the contact I was listening for something to let go. It never quite did.",
        "You make a deal with a damaged car: I'll be gentle, you get me home. We both kept our end.",
    ],
    "pole_to_win": [
        "Never as easy as it looks. You're managing the gap, the tyres, your own mind, every lap.",
        "Controlled, yes -- but control is work. The moment you relax out front is the moment it slips.",
        "From the front you race the track and your own concentration. Both tried to catch me out.",
        "Leading is lonely and it's loud in your own head. You have to keep inventing a rival to chase.",
        "The gap looks comfortable from the outside. Inside, you're defending an empty mirror every lap.",
        "Clean air is a gift, but it's a trap too -- nothing to react to, so you have to drive yourself.",
    ],
    "win_open": [
        "When the gap behind me stopped coming down, I let myself believe it. Not before.",
        "There's a moment the car comes to you and everything else goes quiet. After that, just laps.",
        "I knew when I crossed the line, and not a corner sooner. You never count it before then.",
        "It came together in the middle stint -- the car switched on, and so did I.",
        "You wait your whole life for a day when everything clicks. Today everything clicked.",
        "Honestly? I stopped thinking and started driving, and that was the whole secret of it.",
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
        "charge": ["I danced through the lot of them, and I enjoyed every place. A race you can't take any joy in isn't worth winning -- same as a revolution."],
        "win_open": ["The second it started to feel like fun instead of work, I knew. That's always been my measure of a thing going right."],
    },
    "Mikhail Bakunin": {
        "teammate": ["Hold station for Goldman? She'd never forgive me, and I'd never forgive myself. We tear it down together, the pair of us."],
        "team_orders": ["Hold position for whom? I recognise no authority on that pit wall or anywhere else. We agreed to that before the engines fired -- which is to say, we agreed on nothing, gladly."],
        "charge": ["I destroyed the gap in front of me, then the next, then the next. The urge to tear down is the urge to build, I've always said -- and today I tore down the whole field."],
        "win_open": ["I attacked from lights to flag and never once thought about managing it. Lead, lose it, take it straight back -- that is my whole race plan.",
                     "I have one gear: forward, hard. It went wrong for everyone but me today, which is roughly the plan."],
    },
    "Frantz Fanon": {
        "teammate": ["Closer than the timing screen will ever show. He taught me everything I know about racing. He did not, today, teach me to lift."],
        "team_orders": ["Hold position behind my old teacher? No. I respect him far too much to insult him by lifting."],
        "charge": ["I saw the gaps and I took them. You do not wait to be granted a place out here -- you go and you take it."],
        "win_open": ["It was won the moment I decided not to wait for it. You don't receive a result like this -- you seize it, and you don't apologise for the taking."],
    },
    "Aimé Césaire": {
        "teammate": ["Fanon races like the student who outgrew the lesson. I taught him patience; he has clearly mislaid it. No matter -- it was a fine fight."],
        "pole_to_win": ["I let the hotheads tear past and tear themselves up. Clean lines, cool head -- and there was the win, waiting at the end."],
        "win_open": ["Composed all the way down. I wrote the lap out longhand and it proved quicker than their shouting."],
        "weather": ["I didn't gamble. I read what the track was telling me, calmly, a little ahead of the rest, and acted once I was sure enough. Composure is its own strategy."],
    },
    "Niccolò Machiavelli": {
        "weather": ["The plan accounted for the rain before the first cloud arrived. Fortune merely confirmed what preparation had already decided."],
        "win_open": ["I knew at lights-out. The result was settled on the pit wall on Thursday; today was merely its execution."],
        "charge": ["Cunning, not force. I let them tire themselves fighting, and arrived, unhurried, at the front."],
        "pole_to_win": ["From the front you do not race the others -- you manage them, the gap, the tyres, the appearance of being in control. I had decided this on Thursday. Sunday merely ratified it."],
    },
    "Karl Marx": {
        "charge": ["It was not heroics. It was the conditions, read correctly and applied patiently, lap after lap. The order corrects itself in the end."],
        "win_open": ["History was on my side this afternoon. So were the tyres. Today, the two were the same thing."],
        "weather": ["The material conditions shifted, and I adapted to them before the others noticed they had. That is the whole of strategy."],
        "pole_to_win": ["From the front it is a matter of not squandering the advantage. I administered the lead, lap after lap, and let the result arrive on its own. It always does."],
        "teammate": ["Luxemburg and I want the same world and argue the entire way to it. She'd have seized three moments I let pass. One of us is patient -- and the timing screen can say which of us was right."],
    },
    "Friedrich Nietzsche": {
        "charge": ["I held position exactly never. Forward was the only direction I was willing to recognise, so forward I went."],
        "survival": ["The knock sharpened me. I drove harder after it than most manage with an unmarked car."],
        "team_orders": ["An order to hold station is an order to become less than I am. I did not hear it, and I would not have obeyed it if I had."],
        "win_open": ["I took the lead, and then I simply kept taking. At no corner did I decide I had enough.",
                     "I drove every lap as though I would have to drive it again forever. That tends to be quick."],
    },
    "Simone de Beauvoir": {
        "charge": ["Nothing out there was given to me. I made every place, one decision at a time, and lived with each one."],
        "pole_to_win": ["One is not born in front -- one stays there by choosing well, corner after corner. I chose well."],
        "win_open": ["No single moment was handed to me. I became the winner of this race the way one becomes anything -- by choosing, corner after corner, and refusing to un-choose."],
        "teammate": ["Nietzsche and I share a starting point and almost nothing after it. He drives as though the situation doesn't exist. I never once forgot what I was carrying or where I began -- and I beat him anyway."],
    },
    "Michel Foucault": {
        "weather": ["I'd committed to my move while the rest were still waiting for the wall to commit for them. That one lap was the race."],
        "win_open": ["The track herds everyone onto the same line. I spent the afternoon taking the ones it didn't want me to take."],
        "charge": ["Every place came from a line the circuit was built to keep me off. The track disciplines you onto the obvious path; I refused it, corner after corner, all the way to the front."],
        "pole_to_win": ["Leading only looks like freedom. In truth you're the most watched car out there, every mirror trained on you. I drove the whole race knowing exactly that -- and used it."],
    },
    "Rosa Luxemburg": {
        "weather": ["I didn't wait to be told. I saw the track turning and came in a lap before the pit wall would have called it."],
        "win_open": ["From fourth, I picked my laps and pounced when the gaps came. You can't plan that -- you feel it, and you go."],
        "charge": ["You can't plan a climb like that -- you feel the field shift, you trust it, and you pounce a beat before anyone tells you to. Plan it, and you'd still be sat in fourth."],
        "teammate": ["Marx held me up longer than the opposition did -- waiting, always waiting, for the perfect moment. I made my own. That's the whole argument between us, and today I settled it on the track."],
    },
    "Plato": {
        "pole_to_win": ["I drove the lap I had already seen, complete, in my mind. The rest were chasing a shadow of it."],
        "charge": ["There was no improvising. I had seen the whole climb before lights-out, every pass in its place, and I spent the afternoon making the track agree with what I already knew."],
        "win_open": ["I had driven the whole race in my head before lights-out. Out there I simply matched the picture, corner by corner.",
                     "No surprises. I had seen this race complete before the lights went out, and I spent the afternoon making the world agree with it."],
    },
    "Diogenes": {
        "win_open": ["I expected nothing and arrived first. I recommend the method to the others."],
        "team_orders": ["Team orders? I recognise no authority but my own. The pit wall is welcome to shout into its barrel."],
        "charge": ["No plan, no strategy, nothing to lose -- I had thrown all of that away before the race, the way I throw everything away. Turns out a man with no possessions also has nothing slowing him down."],
    },
    "Jacques Derrida": {
        "win_open": ["I found the gap where their certainty about the line used to be, and was through it before they noticed it had gone."],
        "charge": ["I unpicked their certainty about the racing line until there was a gap where their confidence had been. Then I drove through it."],
        "weather": ["The others waited for the conditions to declare themselves. They never do -- there's no clean moment of certainty to wait for. I stopped waiting and committed, and that lap was the whole race."],
    },
    "Mary Wollstonecraft": {
        "charge": ["I took the chances I was owed and made each one count. No heroics -- just moving forward, place by place, all afternoon."],
        "win_open": ["Clear thinking, lap after lap. I didn't out-muscle anyone today -- I out-reasoned them into the braking zones."],
        "pole_to_win": ["Holding the front is a discipline of the mind, not the right foot. I reasoned through every lap and let nobody tempt me into a mistake. Clear thinking, sustained -- that's the whole of it."],
        "teammate": ["Paine and I argue from the same first principle and arrive at the same place, in our own ways. We raced it cleanly, as equals. I'd insist on nothing less, and so would he."],
    },
    "Thomas Paine": {
        "win_open": ["No cunning, no theatre. Plain courage, plainly applied. It tends to be enough."],
        "survival": ["She was bent, not broken. I shortened the braking, nursed the damage, and counted every last lap down to the flag."],
        "charge": ["No cunning to it. I saw an honest gap, took it, did it again, and made no secret of how. Plain dealing, all the way to the front."],
        "teammate": ["Wollstonecraft and I want the same things and say so plainly. We raced as equals, because that's the only terms either of us would accept."],
    },
    "Herbert Marcuse": {
        "charge": ["Every corner the others backed out of, I stayed in. That is where each of those places came from -- the moment they lifted and I did not."],
        "survival": ["The sensible move was to back out. I declined the sensible move, as is my habit."],
        "win_open": ["It turned the moment I stopped accepting the race as it was handed to me. After that, every place was simply a refusal the others weren't willing to make."],
        "team_orders": ["Hold station? That is precisely the sort of order one exists to refuse. I refused it."],
    },
    "Theodor Adorno": {
        "win_open": ["I drove a controlled, joyless, maximally efficient race. I'm told that is not how one is meant to enjoy it. I enjoyed it regardless."],
        "pole_to_win": ["From the front it is all management -- the gap, the tyres, one's own creeping suspicion of the whole enterprise. I managed all three."],
        "charge": ["I climbed through a field convinced of its own brilliance, picking them off one at a time, and took no pleasure in it. Which is, I'd argue, the only honest way to take pleasure in anything."],
    },
    "Richard Rorty": {
        "weather": ["I went to the inters a lap before the textbook said to. Did it look right? No idea -- it put me up the road, which is all I asked of it."],
        "win_open": ["I stopped wondering whether my line was 'truly' the quickest and just drove the one that kept working. It kept working all day."],
        "charge": ["I stopped asking whether I deserved each place and just took the ones that were there. Worked at the back, worked in the midfield, worked at the front. I don't ask more of an idea than that."],
        "pole_to_win": ["I didn't defend the 'correct' line, I defended whichever one was keeping them behind me. They kept changing. So did I. That's the whole trick."],
    },
}


# =============================================================================
# THE RUNDOWN -- a periodic "state of the race" readout.
# =============================================================================
# A real booth recaps the order every so often, so a listener who's lost the thread
# knows where everyone stands. GENERATED from the live standings (so it differs every
# time the order does); these pools just vary the words around the names, and the
# builder rotates between a few structural frames. (See colour.call_rundown and
# director.rundown.)

RUNDOWN_OPENER = [
    "Let's take stock of the order.",
    "Quick look at how they're running.",
    "Where do we stand, then?",
    "Time for the running order.",
    "Let me run you through the field.",
    "A check on the order as it stands.",
    "Here's how they line up out there.",
    "Right -- the state of play.",
    "For those just joining us, the order.",
]
RUNDOWN_LEADER = [
    "{leader} leads",
    "{leader} out in front",
    "it's {leader} at the head of it",
    "{leader} continues to lead",
    "{leader} sets the pace up front",
    "{leader} still the one to catch",
]
RUNDOWN_POINTS_EDGE = [
    "{name} clings to the final points place in {pos}",
    "{name} holds the last of the points in {pos}",
    "the final point, for now, belongs to {name} in {pos}",
    "{name} hangs on to {pos} -- the last points-paying spot",
    "{name} just inside the points in {pos}, and feeling the pressure",
]
RUNDOWN_BENNY = [
    "Funny how the order looks so tidy and the philosophy so messy.",
    "Half of them don't believe in hierarchy, and yet here we are, ranking them.",
    "Every one of those places hard-won. Or, in two cases, hard-lost.",
    "Read it out all you like -- it'll be different by the hairpin.",
    "Nice and orderly. Give it three laps.",
    "And not a single one of them content with where they are. Good.",
]


# =============================================================================
# THE DEBRIEF -- the post-race show, now driven by the race's ACTUAL arcs.
# =============================================================================
# The spine of the debrief used to be a handful of fixed lines. These pools give the
# booth variety, and -- crucially -- the ARC pools below let it tell the story of the
# fights that actually happened this race (read from the director's RaceMemory), so
# the show is the PAYOFF of what we watched, different every weekend. (See
# colour.debrief and colour._race_stories.)

DEBRIEF_WON_DOMINANT = [
    "Lights to flag, never troubled. {winner} made that look easy, and it never is.",
    "A controlled masterclass from {winner} -- led every lap and was never seriously asked a question.",
    "That was {winner} dictating from the front, start to finish. Imperious.",
    "Untroubled at the front all afternoon. {winner} simply had too much for them.",
    "{winner} led it from green to chequered. No drama, no mistakes, no answer to it.",
]
DEBRIEF_WON_FOUGHT = [
    "Started on pole, but had to fight for it -- the lead changed hands out there. A proper race.",
    "{winner} won from the front, but earned every bit of it -- this one was contested.",
    "Pole to victory, yes, but not a procession. They had to scrap to keep it.",
    "Led at the start and led at the end, but plenty of heat in between. Hard-won.",
]
DEBRIEF_WON_CHARGE = [
    "From {start} on the grid! That's not luck, that's a drive.",
    "Up from {start} to win it -- {winner} carved through the field to do it.",
    "{winner} started {start} and finished first. You don't manage that by accident.",
    "A win from {start} on the grid. That is a proper, old-fashioned charge.",
    "From {start} to the top step. {winner} wanted it more than anybody.",
]
DEBRIEF_STORY_Q = [
    "The battles that defined it?",
    "Story of the race, for you?",
    "What'll we remember from this one?",
    "Where was it really won and lost?",
    "Talk me through the fights, Benny.",
]
DEBRIEF_STORY_OPENER = [
    "Where do I start. A few of them really went at it.",
    "Plenty, as ever. Let me give you the ones that mattered.",
    "A couple of proper scraps out there today.",
    "It wasn't just the win -- the real racing was further back, too.",
    "Some of these will be talked about for a while.",
    "Twenty of the finest minds in history, and not one of them could think their way past the fella in front. Had to race them. I loved it.",
    "Here's the thing about this lot -- they'll disagree about everything except how badly they wanted to win. And it showed.",
]
DEBRIEF_ARC_CONTACT = [
    "{a} and {b} went at it for laps -- and it ended in tears, the pair of them tangling. Inevitable, in the end.",
    "The fight between {a} and {b} could only end one way, and it did: contact, and a lot of arm-waving.",
    "{a} and {b} simply could not be separated -- until they separated each other into the scenery. Shame.",
    "{a} and {b} traded blows until there was a blow too many. That one boiled right over.",
    "Two people that certain they're right, that close together, for that long -- something had to give. {a} and {b} found out what.",
]
DEBRIEF_ARC_UNDERCUT = [
    "{winner} could never get by {loser} on track -- so they went and did it in the pit lane. Clinical.",
    "{loser} held {winner} up for an age, and paid for it at the stops. The undercut, executed perfectly.",
    "{winner} couldn't find a way past {loser} wheel-to-wheel, so they won the fight on the timing screen instead.",
    "All those laps stuck behind {loser}, and {winner} solved it the cold way -- a textbook undercut.",
    "{winner} couldn't out-argue {loser} at the corner, so they out-thought them at the pit wall. The cleverest pass is the one that never touches the track.",
]
DEBRIEF_ARC_EPIC = [
    "{a} and {b} swapped that place more times than I could count. That's racing at its very best.",
    "{a} and {b} gave us the fight of the day -- nose to tail, lap after lap, neither giving an inch.",
    "Go back and watch {a} against {b} again. Wheel to wheel for half the race and clean as you like.",
    "{a} and {b} put on a show -- a proper, old-fashioned scrap that ran and ran.",
    "Neither {a} nor {b} would concede a single corner of the argument. Forty minutes of it, and not a wheel out of place. Magnificent.",
]
DEBRIEF_DOTD = [
    "Has to be {name} -- {gain} made up from the flag. Carved clean through the lot of them.",
    "Drive of the day's {name} for me -- {gain} gained, and not a scratch on the car.",
    "{name}, no question. {gain} up on where they started. Relentless.",
    "Give it to {name} -- {gain} made up. That's a drive you remember.",
]
DEBRIEF_CASUALTY_DOUBLE = [
    "And spare a thought for {a} and {b} -- took each other clean out. That's where it went wrong for two of them.",
    "{a} and {b} won't want to see the replay -- they ended each other's race in one move.",
    "The day fell apart for {a} and {b} together -- contact, and both into retirement. Costly.",
]
DEBRIEF_CASUALTY_SINGLE = [
    "{name}'s afternoon ended early, too. The race doesn't forgive much out there.",
    "Spare a thought for {name} -- out before the flag, and it stings every time.",
    "{name} didn't see the end of it. One of those days where the race bites back.",
]
DEBRIEF_SIGNOFF_PBP = [
    "From {circuit}, that's all from us. Goodnight!",
    "That's the lot from {circuit}. Thanks for joining us -- goodnight!",
    "We'll leave it there from {circuit}. Goodnight, all!",
    "From all of us at {circuit} -- safe home, and goodnight!",
]
DEBRIEF_SIGNOFF_BENNY = [
    "Same again next week, when this lot will once more agree on absolutely nothing.",
    "Drive home safe. Unlike that lot.",
    "Back next time, when they'll find a brand new thing to disagree about at two hundred miles an hour.",
    "Goodnight. And remember -- whatever they preach, they all still wanted to win.",
    "Until next week, when philosophy once again loses to a well-timed pit stop.",
    "Cheerio. Try not to think too hard about any of it.",
]


# =============================================================================
# RACE CONTROL -- the safety car (the first of the neutralisation family).
# =============================================================================
# Deployment is the biggest headline a race throws up -- it wipes every gap and
# reshuffles the strategy -- so it leads the lap; the restart is the crescendo back to
# green. {cause_phrase} is built by the booth from what brought it out. (See
# colour.call_safety_car / call_restart and director._caution_candidates.)

SAFETY_CAR_PBP = [
    "SAFETY CAR! SAFETY CAR! They're scrambling it for {cause_phrase}!",
    "And here comes the safety car -- {cause_phrase}, and the field bunches right up!",
    "Safety car deployed! Every gap wiped in an instant -- {cause_phrase} has done it!",
    "The boards are out -- SAFETY CAR! It's out for {cause_phrase}!",
    "Caution, caution -- the safety car is out for {cause_phrase}!",
]
SAFETY_CAR_COLOUR = [
    "And THAT changes everything. Whoever was leading by miles just lost the lot.",
    "Here's the moment the race resets. Anyone due a stop dives in now -- it's half price under this.",
    "Cruel for the leader, this. All that work, gone -- and a gift for anyone who hadn't stopped.",
    "Free pit stop for half the grid, near enough. Watch the lane -- it'll be chaos.",
    "Twenty seconds of lead, gone in a lap. That's the safety car for you. Brutal.",
]
RESTART_PBP = [
    "Safety car peeling in -- and we are GREEN! Green, green, green -- racing again!",
    "The lights go out on the safety car -- GREEN FLAG! And they are nose to tail!",
    "Here we go -- the restart is ON! Green, and it's a free-for-all into the first corner!",
    "Safety car in this lap -- and RACING resumes! Bunched up and ready to scrap!",
    "GREEN! The race is back on, and there's barely a car-length between any of them!",
]
RESTART_COLOUR = [
    "Right, hold on to something. Everyone's within a second -- this'll be carnage or genius.",
    "This is where races turn. Cold tyres, no gaps, everyone with a sniff. Lovely.",
    "Now we see who timed it. At a restart, the brave ones eat the timid ones.",
    "No hiding now. That cushion at the front? Gone. They have to earn it all over again.",
    "Bunched like that, the next two corners are worth ten normal laps. Watch.",
]
DEBRIEF_CAUTION = [
    "And the safety car had its say, of course -- reset the whole thing and made them race it out again.",
    "Don't forget the caution -- it wiped the leader's gap and turned a procession into a fight.",
    "That safety car was the hinge of the race. Half of what came before barely mattered after it.",
    "The neutralisation changed everyone's afternoon -- some it saved, some it robbed.",
]


# =============================================================================
# RACE CONTROL -- the VSC (full-course yellow) and the RED FLAG.
# =============================================================================
# The lighter and the heavier ends of the neutralisation ladder. The VSC holds the
# gaps and just slows everyone -- a smaller deal, called as such. The RED FLAG stops
# the race outright: the biggest headline there is, with a free tyre change and a
# standing restart to follow. {cause_phrase} is built by the booth. (See
# colour.call_neutralisation / call_resumption.)

VSC_PBP = [
    "Virtual safety car -- VSC, VSC! {cause_phrase}, everyone slow down!",
    "Full-course yellow deployed for {cause_phrase} -- delta time on, no overtaking!",
    "VSC is out for {cause_phrase} -- they hold station, gaps frozen where they are.",
    "Yellows all round -- the VSC is on for {cause_phrase}. Everyone off the throttle.",
    "It's a virtual safety car for {cause_phrase} -- not the full car, but they must slow.",
]
VSC_COLOUR = [
    "Kinder than the real thing, this. The leader keeps their cushion -- gaps don't move.",
    "Still a chance to pit cheap, mind. Anyone due a stop will be thinking about it.",
    "No bunching, so no lottery. The order's held -- it's just everybody, slower.",
    "Less drama than a safety car, but the pit wall's still doing sums.",
    "Gaps preserved -- so whoever was clear stays clear. That's the difference.",
]
VSC_END_PBP = [
    "And the VSC is withdrawn -- green flag, racing resumes!",
    "Delta off -- we're GREEN again, and they pick up where they left off!",
    "Full-course yellow over -- green, green, and back up to speed!",
    "VSC ending -- and they're racing once more, gaps intact!",
]
VSC_END_COLOUR = [
    "No restart shuffle here -- everyone just stands on it again. Tidy.",
    "Straight back to it. Nobody gained, nobody lost -- as it should be.",
    "And we resume exactly as we were. The VSC giveth nothing and taketh nothing.",
    "Back to green with the order untouched. On we go.",
]
RED_FLAG_PBP = [
    "RED FLAG! RED FLAG! The race is STOPPED -- {cause_phrase} has brought it to a halt!",
    "It's a RED FLAG! They're stopping the Grand Prix -- {cause_phrase}, and that's too much to clear under green!",
    "Red flag! The race is suspended -- {cause_phrase}, and the cars are heading for the grid!",
    "STOPPED! A red flag for {cause_phrase} -- the whole race comes to a standstill!",
]
RED_FLAG_COLOUR = [
    "And here's the big one. Free tyre change for everybody -- and that is a GIFT for anyone who hadn't stopped.",
    "This rips the race up. Whoever paid full price for a stop just watched it count for nothing.",
    "Fresh rubber for the lot of them, for free. The strategists who gambled long just won the lottery.",
    "Everything resets. New tyres, a standing start, and all that track position back in the melting pot.",
    "The leader will hate this. The cushion's gone, the tyres are equal, and it's a drag race from the grid.",
]
RED_RESTART_PBP = [
    "They're lined up on the grid -- lights coming on for the standing restart... and GREEN! GO, GO, GO!",
    "Standing restart! The lights go out -- and it's a second Grand Prix start, right here!",
    "Here we go again -- standing start, lights out, and they SCRAMBLE off the line!",
    "The race resumes from the grid -- lights... away! A clean getaway or chaos, let's see!",
]
RED_RESTART_COLOUR = [
    "Cold tyres, a clutch, and one chance to nail it. This is where the brave are made.",
    "A whole new launch lottery. Whoever bogs down here loses everything they fought for.",
    "Standing start -- so it's all about the getaway now. Nail it or lose three places.",
    "This is the start all over again, and starts are where the carnage lives. Hold tight.",
]
DEBRIEF_RED_FLAG = [
    "And of course the red flag tore it all up -- free tyres, a standing restart, and a brand new race from there.",
    "That red flag was the whole story. Everything before the stoppage may as well have been a different afternoon.",
    "You can't talk about this one without the red flag -- it handed fresh tyres to everyone and reset the lot.",
    "The stoppage decided it. Whoever read that standing restart best walked away with the spoils.",
]
