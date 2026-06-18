"""The booth -- the two voices and the logic that decides who says what.

display.render_* is the lap caller's FACTUAL line (a pass, a crash, a stop). This
module wraps two things around that:

  * the PERSONAS -- who is in the booth. The lore speaks in roles ("pbp", "colour");
    here we map those roles to names, so renaming the commentators, or swapping in a
    third, is a one-line change. `voice()` stamps each feed line with its speaker, so
    the whole feed reads as a transcript of two people rather than anonymous calls.

  * the director (Booth) -- a second consumer of the very same event stream the lap
    caller reads. Given a moment it reaches into lore.py for a BIT (a one-liner or a
    multi-turn exchange), prefers the rare relational gold over generic filler, and
    remembers what it has used so nothing repeats in a race. The selection is a
    PRIORITY policy, the same shape as the "is this pass worth calling?" threshold.

The marquee hook is the green-flag conversation: on a lap with no events, a real
booth doesn't fire a one-liner -- it runs a topic and develops it. So next_chatter
advances a multi-turn DISCUSSION a beat at a time across the quiet laps, pausing
when the racing interrupts and resuming after. The lap caller has ALREADY voiced the
factual line by the time a Bit plays, so an overtake Bit is the REACTION to the
move, never a re-call of it.
"""

import random

from drivers import GRID
from lore import (DRIVER_LORE, PAIR_LORE, TRACK_LORE, DISCUSSIONS,
                  GENERIC_INCIDENT, GENERIC_OVERTAKE, GENERIC_PIT,
                  Bit, banter, PODIUM_QUOTES, PODIUM_QUOTE_FALLBACK,
                  # the calls -- Phill's factual lines, now owned by the booth
                  START_CALLS, OVERTAKE_CALLS, BATTLE_CALLS, SOLO_RETIRE,
                  OVERLIMIT_CALLS, DAMAGE_FAIL_CALLS, COLLISION_CALLS,
                  CAUSE_PHRASE, SOLO_FLOURISH, CONTACT_WORD, PIT_CALLS, UNDERCUT_CALLS,
                  # the podium interview
                  PODIUM_HANDOFF, PODIUM_QUESTIONS, PODIUM_CLOSER_Q,
                  PODIUM_ANSWER_GENERIC, PODIUM_ANSWERS)

_DRIVER_BY_NAME = {d.name: d for d in GRID}

# Each driver's teammate (same team) -- so the podium reporter can ask about an
# intra-team scrap by name. Built once from the grid data.
_TEAMMATE = {}
for _d in GRID:
    _mates = [x.name for x in GRID if x.team == _d.team and x.name != _d.name]
    _TEAMMATE[_d.name] = _mates[0] if _mates else None


# Who's in the booth. Roles -> names. Change these two strings and the whole feed
# re-casts itself; add a third role here (and turns in lore.py) for a three-hander.
PERSONAS = {
    "pbp":    "Phill",    # the lap caller: excitable, plummy, sets his man up
    "colour": "Benny",    # the sidekick: ex-racer, dry, thinks the philosophy is daft
    "report": "Suze",     # the pit-lane reporter: heard only on the podium, conducts the interviews
}
_TAG_WIDTH = max(len(n) for n in PERSONAS.values()) + 1   # room for the colon


def _speaker(role):
    """A role maps to a persona name; anything else (e.g. a driver's name in a
    podium quote) is taken as a literal speaker label."""
    return PERSONAS.get(role, role)


def voice(lap, role, text):
    """One in-race feed line, stamped with its speaker -- so the feed reads as a
    transcript. The speaker label is what tells the voices apart; no '>>' marker."""
    tag = _speaker(role).upper() + ":"
    return f"  L{lap:>2}  {tag:<{_TAG_WIDTH}} {text}"


def voice_show(role, text):
    """A line in a pre/post-race SHOW -- same speaker stamp, but no lap number, since
    the shows happen off the clock (before lights-out / after the flag)."""
    tag = _speaker(role).upper() + ":"
    return f"  {tag:<{_TAG_WIDTH}} {text}"


# Spoken-friendly number words -- the feed says "five laps to go" and "up eleven
# places", never a bare digit, so a text-to-speech engine reads clean prose.
_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
         "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
         "eighty", "ninety"]
_ORDINAL = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
            6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth",
            11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth",
            15: "fifteenth", 16: "sixteenth", 17: "seventeenth", 18: "eighteenth",
            19: "nineteenth", 20: "twentieth"}


def _spell(n):
    """A cardinal number in words, 0-99 -- so a spoken line never shows a digit.
    (Above ninety-nine it falls back to the numeral; no race figure gets there.)"""
    if not isinstance(n, int) or n < 0 or n > 99:
        return str(n)
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] + (f"-{_ONES[ones]}" if ones else "")


def _ord(n):
    return _ORDINAL.get(n, f"{n}th")


def _at(loc):
    """' at the Parabolica' when we know the corner, '' when we don't."""
    return f" at {loc}" if loc else ""


# How often an ORDINARY pass (no authored rivalry) earns a line about the passer.
# A genuine rivalry always gets called; this keeps us from reacting to every lunge.
PLAIN_OVERTAKE_COLOUR = 0.35

# Two cars trading the same place within this many laps reads as ONE ongoing scrap,
# not a string of identical "X passes Y" calls. The booth collapses the flicker.
BATTLE_WINDOW = 3

# How many turns of the running DISCUSSION the booth delivers per quiet lap. Two
# keeps a question-and-answer beat together rather than stranding a tee-up a lap from
# its payoff; the rest carries over to the next quiet lap, so a topic unfolds across
# the green-flag spell and gets interrupted by the racing, like a real booth.
CHATTER_TURNS_PER_LAP = 2

# The closing laps get their OWN register: the booth builds tension toward the flag
# whether or not anything is happening, so the run-in never goes quiet. These lines
# are GENERATED from race state (laps left, the gap), so unlike the authored lull
# pool they can never run dry, and they escalate as the laps tick down.
RUNIN_LAPS = 6

# Run-in phrasings by how close the fight for the lead is. {count} is the spoken
# countdown ("Five laps to go"), {ldr}/{sec} the leader and chaser. Several per
# bucket, and the booth avoids using the same one twice in a row (see _fresh_runin).
_RUNIN = {
    "close": {      # the lead is under real threat -- a nail-biter
        "pbp": ["{count} -- and {sec} is ALL OVER the back of {ldr}!",
                "{count}, and this is on a knife edge -- {sec} right with {ldr}!",
                "{count}, and {sec} has thrown everything at {ldr} -- this is for the win!",
                "{count} -- {sec} filling {ldr}'s mirrors, this is going to the wire!",
                "{count}, and you cannot separate them -- {ldr} and {sec}, nose to tail!"],
        "colour": ["He can see him in the mirrors now. This is going to be desperate.",
                   "One lock-up, one twitch, and it's gone. Edge of your seat.",
                   "Everything on the line here. Nobody is sitting down for this.",
                   "Whoever wants it more over these last few corners. That simple, that brutal.",
                   "Forty years I've done this and my heart's still going. Look at it."],
    },
    "closing": {    # the gap is coming down, but maybe not in time
        "pbp": ["{count} -- {sec} closing on {ldr}, but is there enough road left?!",
                "{count}, and the gap is coming DOWN -- {ldr} will not want to see this!",
                "{count} -- {ldr} still ahead, but {sec} can smell it now!",
                "{count}, and {sec} has found something -- {ldr}'s lead is shrinking!",
                "{count} -- it's {ldr}, but {sec} is reeling them in hand over fist!"],
        "colour": ["Tyres gone off, maybe. Whatever it is, that lead's not safe.",
                   "A few laps ago you'd have called it done. Not any more.",
                   "This could run all the way to the line, you know.",
                   "The maths is tight. A backmarker at the wrong moment and it's on.",
                   "He'll be counting corners now, not laps. Praying for the flag."],
    },
    "clear": {      # a comfortable lead -- but the occasion still lifts the crowd
        "pbp": ["{count}, and {ldr} looks to have this in hand -- but LISTEN to that crowd!",
                "{count} -- {ldr} out on their own up front, and the grandstands are already up!",
                "{count}, and {ldr} is sailing toward it -- the whole place rising to its feet!",
                "{count} -- daylight for {ldr}, and you can hear the roar building already!",
                "{count}, and barring disaster this is {ldr}'s -- the ovation's already starting!"],
        "colour": ["Doesn't matter who's where. You stand and applaud a drive like that.",
                   "Procession or not, that's history happening out front. Up they get.",
                   "They know exactly what they're watching. Whole place on its feet.",
                   "Win like this and the ovation's a formality. Listen to them.",
                   "Nothing left to decide up front now -- just a lap of honour in all but name."],
    },
}

# Weather CALLS -- spoken when the conditions cross a tyre crossover. Like the run-in,
# this is reactive to live state (the booth says it because it just happened), so it's
# inherently fresh; several phrasings per change keep even back-to-back showers varied.
_WEATHER = {
    "rain_begins": {
        "pbp": ["And it's starting to rain! Spots of rain appearing across the circuit!",
                "Rain! Here it comes -- and this track will go greasy in a hurry!",
                "The rain everyone's been watching the skies for -- it's arriving, right now!"],
        "colour": ["Decision time. Slicks are living on borrowed laps from here.",
                   "This is where the strategists earn their keep. Intermediates, and soon.",
                   "The brave stay out a lap too long. The smart are already boxing."],
    },
    "rain_intensifies": {
        "pbp": ["It's really coming down now -- this has become a proper downpour!",
                "The heavens have opened! This is full wet-weather territory now!"],
        "colour": ["Inters won't live in this. They need the full wets, every one of them.",
                   "You can barely see out there. This is survival now, not racing."],
    },
    "rain_eases": {
        "pbp": ["The rain's easing off -- and a dry line just might start to appear!",
                "It's backing off now -- the worst of this may be behind them!"],
        "colour": ["Back to inters, and whoever reads the next few laps right gets the jump.",
                   "Now it flips the other way -- too early onto slicks and you're a passenger."],
    },
    "track_dry": {
        "pbp": ["And the track is dry enough for slicks again -- the gamble is ON!",
                "Slicks are coming back! The racing line has come good!"],
        "colour": ["The crossover is the whole race now. A lap too early and it's chaos.",
                   "First one brave enough for slicks flies -- if they keep it out of the wall."],
    },
}

# Calm-weather AMBIENT -- the filler that makes the user's wish come true: something
# to say even when the weather is lovely and nothing is happening. Generated from the
# temperatures and the sky, bucketed, and never repeated back-to-back from a bucket.
_AMBIENT = {
    "hot": [
        ("Track temperature really climbing now -- well up into the forties.",
         "Hot as that, the tyres give up early. Whoever manages them wins this."),
        ("They're reporting a scorching surface out there this afternoon.",
         "Cooking, that tarmac. The second stint becomes a fight with the rear tyres."),
        ("Heat haze shimmering off the start-finish straight now.",
         "On a track this hot it's not about outright pace -- it's about who's kindest to the rubber."),
        ("The sun is full out and that asphalt is baking.",
         "Thermal degradation, this. They'll be nursing those tyres home, you watch."),
    ],
    "cold": [
        ("A cool, grey afternoon, and a cold track underneath them.",
         "Cold as this, they'll struggle to switch the tyres on. Out-laps will be lurid."),
        ("Air temperature has dropped -- not much warmth in this track at all.",
         "This is when the snaps come from nowhere. No heat in the rubber, no warning."),
        ("Grey skies, a chilly wind down the straight, a cold surface.",
         "Graining weather, this. The fronts will go off long before the rears."),
        ("Barely double figures on the air temperature now.",
         "They'll be weaving like mad on the warm-up laps just to find some grip."),
    ],
    "fair": [
        ("Glorious conditions over the circuit -- barely a cloud up there.",
         "Perfect for it. No hiding place out there today, just racing."),
        ("Warm, settled, a lovely day for a Grand Prix.",
         "Textbook conditions. This is where the genuinely quick ones simply rise."),
        ("Still bone dry, and the skies are staying kind for now.",
         "Long may it last -- though they are keeping an eye on those clouds over the hills."),
        ("A gentle breeze, a warm track, ideal racing weather.",
         "Nothing to blame but yourself in conditions like these. Pure driving."),
        ("Settled and dry, the perfect stage for them.",
         "When it's this benign, the grid order tends to tell the truth. No lottery today."),
    ],
    "greasy": [
        ("Just a few spots in the air, and the track's gone slick and shiny.",
         "Treacherous, this in-between. Slicks underneath them, but no faith in them at all."),
        ("That surface is glistening now -- caught between dry and wet.",
         "Worst of both worlds, this. Too wet to attack, too dry to box. Horrible."),
        ("A greasy sheen across the whole circuit now.",
         "One wrong throttle input and they're gone. Nobody trusts the grip an inch."),
    ],
    "damp": [
        ("Damp all the way round, spray kicking up behind every car.",
         "Intermediate weather through and through. Tip-toe stuff, this."),
        ("A greasy, damp circuit, the inters just about coping.",
         "It's all about commitment now. Hesitate and you're nowhere; overdo it and you're gone."),
        ("Persistent drizzle, the track soaked but not flooded.",
         "Prime intermediate conditions. The feel for it now is everything -- you can't fake this."),
    ],
    "wet": [
        ("Standing water in places now -- great plumes of spray off the back of them!",
         "Anyone who keeps it on the island in this earns a medal, never mind a trophy."),
        ("It is streaming out there, rivers running across the racing line.",
         "Visibility nil, aquaplaning everywhere. This is as hard as their job ever gets."),
        ("Full wets and still struggling -- it is biblical out there now.",
         "At this point it's not racing, it's bravery. Half of them can't see the car ahead."),
    ],
}


class Booth:
    """One per race. Holds the circuit and the memory of which Bits it has used."""

    def __init__(self, track):
        self.circuit = track.circuit if track else ""
        self.used = set()
        self._last_runin = {}                       # (bucket, role) -> last template index used
        self._last_weather = {}                     # change -> (last pbp idx, last colour idx)
        self._ambient_used = {}                     # bucket -> set of pair indices already aired
        self._thread = []                           # remaining turns of the active discussion
        self._used_threads = set()                  # threads already run this race
        self._last_about = frozenset()              # subjects of the last thread (avoid back-to-back)
        self._battles = {}                          # frozenset(pair) -> {lap, swaps}: collapse trading places

    def _pick(self, bits, tags):
        """Keep Bits whose trigger is in `tags` and that we haven't used, then choose
        one (weighted). Mark it used; return it, or None. Marking is what stops a Bit
        ever repeating within a race."""
        pool = [b for b in bits if b.when in tags and b not in self.used]
        if not pool:
            return None
        chosen = random.choices(pool, weights=[b.weight for b in pool])[0]
        self.used.add(chosen)
        return chosen

    def _pair_any_order(self, a, b, tags):
        """Pair lore that reads either way (a rivalry) -- try both orderings."""
        return (self._pick(PAIR_LORE.get((a, b), []), tags)
                or self._pick(PAIR_LORE.get((b, a), []), tags))

    # --- the calls: Phill's FACTUAL lines, with variety and spoken numbers -----
    # The booth now owns these too (they used to live in display.render_*). Every
    # call is drawn from a deep pool, never repeated back-to-back (_fresh), and
    # every number is spelled, so the lap caller reads as clean as the colour man.
    def call_overtake(self, ov, lap):
        """Phill's call for a completed pass. A re-pass between two cars already
        scrapping is collapsed into one ongoing-battle line, so trading places
        reads as a fight, not a stutter of identical calls."""
        if ov.location == "the start":
            return self._call_start(ov)
        at = _at(ov.location)
        pos_ord = _ord(ov.position)
        pair = frozenset((ov.passer, ov.passed))
        prev = self._battles.get(pair)
        if prev and lap - prev["lap"] <= BATTLE_WINDOW:        # they're at it again
            prev["swaps"] += 1
            prev["lap"] = lap
            bucket = "again" if prev["swaps"] == 1 else "ongoing"
            return self._fresh(f"_battle_{bucket}", BATTLE_CALLS[bucket]).format(
                driver=ov.passer, other=ov.passed, pos=pos_ord, at=at)
        self._battles[pair] = {"lap": lap, "swaps": 0}         # a fresh pass: remember it
        bucket = "lead" if ov.position == 1 else "podium" if ov.position <= 3 else "points"
        return self._fresh(f"_ot_{bucket}", OVERTAKE_CALLS[bucket]).format(
            driver=ov.passer, other=ov.passed, pos=pos_ord, at=at)

    def _call_start(self, ov):
        """The getaway off the line, scaled by how big the launch was."""
        if ov.position == 1:
            bucket = "lead"
        elif ov.places_gained >= 4:
            bucket = "flier"
        elif ov.places_gained >= 2:
            bucket = "good"
        else:
            bucket = "edge"
        return self._fresh(f"_start_{bucket}", START_CALLS[bucket]).format(
            driver=ov.passer, pos=_ord(ov.position), gained=_spell(ov.places_gained))

    def call_incident(self, inc):
        """Phill's call for a mistake, a collision, or a retirement."""
        at = _at(inc.location)
        d = inc.driver_name
        if inc.cause == "over the limit":
            return self._fresh("_inc_depth", OVERLIMIT_CALLS).format(driver=d, at=at)
        if inc.cause == "damage failure":
            return self._fresh("_inc_dmg", DAMAGE_FAIL_CALLS).format(driver=d)
        if inc.cause == "collision":
            if inc.retirement and inc.other_retired:
                bucket = "both_out"
            elif inc.other_retired:
                bucket = "other_out"
            elif inc.retirement:
                bucket = "self_out"
            else:
                bucket = "both_go"
            return self._fresh(f"_col_{bucket}", COLLISION_CALLS[bucket]).format(
                driver=d, other=inc.other_name, at=at,
                severity=inc.severity, word=CONTACT_WORD[inc.severity])
        # solo error: a cause phrasing, then either a retirement tag or a flourish
        phrase = self._fresh(f"_cause_{inc.cause}", CAUSE_PHRASE.get(inc.cause, [inc.cause]))
        if inc.retirement:
            return self._fresh("_solo_retire", SOLO_RETIRE).format(
                driver=d, phrase=phrase, at=at, severity=inc.severity)
        flourish = self._fresh(f"_flour_{inc.severity}", SOLO_FLOURISH[inc.severity])
        return f"{d} {phrase}{at} -- {flourish}"

    def call_pit(self, ps):
        """Phill's call for a pit stop -- spoken, with the stint length in words."""
        onto = f" onto {ps.compound}s" if ps.compound else ""
        stint = _spell(ps.old_stint)
        if ps.stop_number >= 2:
            return self._fresh("_pit_again", PIT_CALLS["again"]).format(
                driver=ps.driver_name, onto=onto, stint=stint, ord=_ord(ps.stop_number))
        return self._fresh("_pit_first", PIT_CALLS["first"]).format(
            driver=ps.driver_name, onto=onto, stint=stint)

    def call_undercut(self, uc):
        """Phill's call for an undercut completing -- a pass won in the pit lane."""
        earlier = "a lap" if uc.laps_earlier == 1 else f"{_spell(uc.laps_earlier)} laps"
        bucket = "lead" if uc.position == 1 else "points"
        return self._fresh(f"_uc_{bucket}", UNDERCUT_CALLS[bucket]).format(
            driver=uc.undercutter, other=uc.victim, earlier=earlier, pos=_ord(uc.position))

    def lights_out(self):
        """The green-flag call -- the SAME words every time, because some moments are
        ritual and the regulars want to hear them. Phill marks the start; the booth
        supplies the circuit name."""
        return f"The lights are off, and we go racing in {self.circuit}!"

    # --- event-triggered colour ---------------------------------------------
    def for_overtake(self, ov):
        """The booth's reaction to a completed pass. A real rivalry is the money
        moment and always plays; the start gets a quick character quip only for the
        drivers who have one; an ordinary pass gets a reaction only sometimes, drawn
        from the passer's own lines or, failing that, a generic one for variety."""
        if ov.location == "the start":
            return self._pick(DRIVER_LORE.get(ov.passer, []), {"start"})
        # Directional: the lore names who passed whom, so only this ordering fits.
        gold = self._pick(PAIR_LORE.get((ov.passer, ov.passed), []), {"overtake"})
        if gold:
            return gold
        if random.random() < PLAIN_OVERTAKE_COLOUR:
            return (self._pick(DRIVER_LORE.get(ov.passer, []), {"overtake", "any"})
                    or self._pick(GENERIC_OVERTAKE, {"overtake"}))
        return None

    def for_incident(self, inc):
        """Reaction to a mistake or a retirement -- prefer the retirement-specific
        line when the car is actually out, then the driver's own 'incident' line,
        then a generic one so the colour man never repeats himself across crashes."""
        pool = DRIVER_LORE.get(inc.driver_name, [])
        if inc.retirement:
            return (self._pick(pool, {"retirement"})
                    or self._pick(pool, {"incident"})
                    or self._pick(GENERIC_INCIDENT, {"incident"})
                    or self._pick(pool, {"any"}))
        return (self._pick(pool, {"incident"})
                or self._pick(GENERIC_INCIDENT, {"incident"})
                or self._pick(pool, {"any"}))

    def for_pit(self, ps):
        """The booth's occasional dry word on a pit stop. Most stops pass without
        comment; now and then the driver's own line, or a generic one, gets an airing.
        The caller decides how often to ask (a stop every lap would be noise)."""
        return (self._pick(DRIVER_LORE.get(ps.driver_name, []), {"pit"})
                or self._pick(GENERIC_PIT, {"pit"}))

    # --- the quiet laps: a running DISCUSSION, a beat at a time -------------
    def next_chatter(self, standings, lap):
        """The green-flag conversation. Advance the active discussion by a beat (a
        couple of turns); when it's finished, pick a NEW thread relevant to who's
        actually racing. Returns a list of (role, line) for this lap -- empty only
        if every thread is spent. Because a thread unfolds over several laps and is
        paused (not dropped) when the racing interrupts, it reads as a real
        conversation rather than a one-liner fired and forgotten."""
        if not self._thread:
            thread = self._choose_thread(standings)
            if thread is None:
                return []
            self._used_threads.add(thread)
            self._last_about = frozenset(thread.about)
            self._thread = list(thread.turns)
        beat = self._thread[:CHATTER_TURNS_PER_LAP]
        self._thread = self._thread[CHATTER_TURNS_PER_LAP:]
        return beat

    def _choose_thread(self, standings):
        """Pick the next discussion. Prefer threads about a current battle (two cars
        running nose-to-tail) or the leader; let general and track threads in for
        variety; never reuse a thread, and avoid the same subject twice running. If
        the whole pool is spent, recycle it rather than fall silent."""
        running = [s for s in standings if not s.retired]
        if not running:
            return None
        running_names = {s.name for s in running}
        leader = running[0].name
        battling = {frozenset((a.name, b.name)) for a, b in zip(running, running[1:])}

        def candidates():
            scored = []
            for t in DISCUSSIONS:
                if t in self._used_threads:
                    continue
                if t.track and t.track != self.circuit:
                    continue
                if t.about and not set(t.about) <= running_names:
                    continue                            # every named subject must be out there
                score = 1.0
                if t.track == self.circuit:
                    score += 1.5
                if t.about and leader in t.about:
                    score += 3.0
                if len(t.about) >= 2 and frozenset(t.about[:2]) in battling:
                    score += 5.0                        # a live wheel-to-wheel rivalry: talk about it
                if t.about and self._last_about & set(t.about):
                    score *= 0.25                       # just covered this lot -- move on
                scored.append((score, t))
            return scored

        scored = candidates()
        if not scored:                                  # pool spent -- recycle, don't go quiet
            self._used_threads.clear()
            scored = candidates()
        if not scored:
            return None
        return random.choices([t for _, t in scored],
                              weights=[s for s, _ in scored])[0]

    # --- the run to the flag: keep the crowd alive no matter what -----------
    def for_runin(self, standings, lap, total_laps):
        """The closing laps. Build the tension from the live race state -- how many
        laps remain and how big the lead is -- so the run-in is always lively and
        never repeats stale lines. A nail-biter and a procession get different
        words, but BOTH end with the crowd on their feet (that's the whole point:
        the audience should want to stand up whoever wins)."""
        to_go = total_laps - lap
        if not 1 <= to_go <= RUNIN_LAPS:
            return None
        running = [s for s in standings if not s.retired]
        if not running:
            return None
        leader = running[0]
        second = running[1] if len(running) > 1 else None
        margin = second.gap_to_leader if second else None

        if second is not None and margin is not None and margin < 1.2:
            bucket = "close"
        elif second is not None and margin is not None and margin < 4.0:
            bucket = "closing"
        else:
            bucket = "clear"

        count = f"{_spell(to_go).capitalize()} {'lap' if to_go == 1 else 'laps'} to go"
        fmt = {"count": count, "ldr": leader.name, "sec": second.name if second else ""}
        vale = self._fresh_runin(bucket, "pbp").format(**fmt)
        benny = self._fresh_runin(bucket, "colour").format(**fmt)
        return banter([("pbp", vale), ("colour", benny)])

    def _fresh_runin(self, bucket, role):
        """Pick a run-in template, never the same one twice running for this bucket
        and speaker -- so a long procession doesn't echo the same line every lap."""
        options = _RUNIN[bucket][role]
        last = self._last_runin.get((bucket, role))
        pool = [i for i in range(len(options)) if i != last] or list(range(len(options)))
        i = random.choice(pool)
        self._last_runin[(bucket, role)] = i
        return options[i]

    def for_finish(self, standings):
        """The flag. The winner's moment, always called -- a race never ends on
        silence. Deep pools, picked fresh, so the chequered flag doesn't read the
        same way two races running."""
        running = [s for s in standings if not s.retired]
        if not running:
            return None
        w = running[0]
        vale = self._fresh("_finish_pbp", [
            f"{w.name} takes the chequered flag -- WINS the Grand Prix!",
            f"It's {w.name}! Across the line to take it -- what a result for {w.team}!",
            f"The flag is OUT, and {w.name} has WON it -- a famous day for {w.team}!",
            f"{w.name} brings it home -- victory, and the {w.team} garage erupts!",
            f"And it's {w.name} who takes the win -- they have been imperious today!",
            f"{w.name} crosses the line first -- the chequered flag, and the Grand Prix, is theirs!",
        ])
        benny = self._fresh("_finish_colour", [
            "Get up out of your seats. That is how you win a motor race.",
            "Brilliant. Argue about the philosophy later -- right now, just applaud.",
            "Deserved every inch of that. Cracking drive.",
            "You don't see many better than that. Take a bow.",
            "Whatever you think of their ideas, you cannot fault the driving. Superb.",
            "Flawless when it mattered. That's a winner's afternoon, start to finish.",
            "They thought, they drove, they won. In that order. Lovely to watch.",
        ])
        return banter([("pbp", vale), ("colour", benny)])

    def _fresh(self, key, options):
        """Pick from `options`, avoiding the index used last time for this key -- the
        generic no-immediate-repeat used by the run-in and the flag."""
        last = self._last_runin.get(key)
        pool = [i for i in range(len(options)) if i != last] or list(range(len(options)))
        i = random.choice(pool)
        self._last_runin[key] = i
        return options[i]

    # --- weather: the live conditions, as commentary ------------------------
    def for_weather(self, change):
        """A weather CALL -- the track has crossed a tyre crossover (rain begins,
        intensifies, eases, or dries). Reactive to the moment, so always fresh; the
        booth avoids repeating a phrasing back-to-back across a flickering shower."""
        bucket = _WEATHER.get(change)
        if not bucket:
            return None
        last_p, last_c = self._last_weather.get(change, (None, None))
        pj = [i for i in range(len(bucket["pbp"])) if i != last_p] or list(range(len(bucket["pbp"])))
        cj = [i for i in range(len(bucket["colour"])) if i != last_c] or list(range(len(bucket["colour"])))
        pi, ci = random.choice(pj), random.choice(cj)
        self._last_weather[change] = (pi, ci)
        return banter([("pbp", bucket["pbp"][pi]), ("colour", bucket["colour"][ci])])

    def weather_ambient(self, conditions):
        """Quiet-lap filler GENERATED from the conditions -- temps and sky on a dry
        day, the state of the track on a wet one. This is the answer to 'give them
        something to say even when the weather is calm': there is always a reading to
        remark on, and it drifts lap to lap so it never lands the same way twice."""
        if conditions is None:
            return None
        label = conditions.label
        if label == "dry":
            if conditions.track_temp >= 40:
                bucket = "hot"
            elif conditions.track_temp <= 16:
                bucket = "cold"
            else:
                bucket = "fair"
        else:
            bucket = label                       # "greasy" | "damp" | "wet"
        pairs = _AMBIENT.get(bucket)
        if not pairs:
            return None
        # Air every line in a bucket once before any of them comes round again -- so a
        # long, settled afternoon works through all its remarks instead of echoing two.
        used = self._ambient_used.setdefault(bucket, set())
        if len(used) >= len(pairs):
            used.clear()
        pool = [i for i in range(len(pairs)) if i not in used]
        i = random.choice(pool)
        used.add(i)
        pbp_line, colour_line = pairs[i]
        return banter([("pbp", pbp_line), ("colour", colour_line)])

    # --- the shows: off-clock segments before and after the race ------------
    def preview(self, quali, track):
        """The 'Countdown to Green': set the scene, the track's history, the top of
        the grid, and what to watch. Returns a list of (role, line) turns the show
        plays in order. Generated from the qualifying result and the track's own
        numbers, so it's always accurate to THIS weekend."""
        qualifiers = [d for d, lap, ok in quali if ok]
        turns = [("pbp", f"Welcome to {track.circuit} -- we are set for the {track.name}.")]

        hist = self._pick(TRACK_LORE.get(self.circuit, []), {"any"})
        if hist:
            turns.extend(hist.turns)

        if qualifiers:
            pole = qualifiers[0]
            if len(qualifiers) > 1:
                turns.append(("pbp", f"Pole position goes to {pole.name} for {pole.team}, "
                                     f"{qualifiers[1].name} alongside on the front row."))
            else:
                turns.append(("pbp", f"Pole position: {pole.name} for {pole.team}."))
            turns.append(("colour", self._pole_read(pole)))
            watch = self._watch_name(qualifiers)
            if watch:
                turns.append(("colour", watch))

        turns.append(("pbp", "So what are we watching for, Benny?"))
        turns.append(("colour", self._track_tips(track)))
        turns.append(("pbp", "Lights out is moments away. Stand by."))
        return turns

    def debrief(self, summary, history, track):
        """The post-race show: how it was won, where strategy turned, the drive of
        the day, the casualties, and quick quotes from the podium. Returns a list of
        (role, line) turns -- with the podium lines spoken by the DRIVERS themselves."""
        s = summary
        turns = [("pbp", f"And that's the chequered flag at {s.circuit} -- "
                         f"{s.winner} wins it for {s.team}!")]

        # How it was won.
        if s.winner_from == 1 and s.lead_changes == 0:
            turns.append(("colour", f"Lights to flag, never troubled. {s.winner} made that look "
                                    f"easy, and it never is."))
        elif s.winner_from == 1:
            turns.append(("colour", "Started on pole, but had to fight for it -- lead changed hands "
                                    "out there. A proper race."))
        else:
            turns.append(("colour", f"From {_ord(s.winner_from)} on the grid! That's not luck, "
                                    f"that's a drive."))

        # Where strategy turned.
        if s.undercuts_count:
            turns.append(("pbp", "And strategy played its part?"))
            turns.append(("colour", f"The undercut was the weapon today -- {_spell(s.undercuts_count)} "
                                    f"of them paid off in the pit lane. Won and lost on the timing "
                                    f"screen, not on the road."))
        elif s.lead_changes >= 3:
            turns.append(("colour", "Won on track, this one -- wheel to wheel, none of your "
                                    "pit-lane chess. Loved it."))

        # The drive of the day.
        if s.drive_of_the_day:
            name, gained = s.drive_of_the_day
            turns.append(("pbp", "Drive of the day?"))
            turns.append(("colour", f"Has to be {name} -- up {_spell(gained)} place"
                                    f"{'s' if gained != 1 else ''} from the start. Carved clean "
                                    f"through the lot of them."))

        # Where it went wrong.
        if s.double_dnfs:
            a, b, _lap, _loc = s.double_dnfs[0]
            turns.append(("colour", f"And spare a thought for {a} and {b} -- took each other clean "
                                    f"out. That's where it all went wrong for two of them."))
        elif s.retirements:
            turns.append(("colour", f"{s.retirements[0][0]}'s afternoon ended early, too. The race "
                                    f"doesn't forgive much out there."))

        # The podium interview -- a real give-and-take, conducted by the pit-lane
        # reporter, with questions drawn from THIS driver's race. Racing first; the
        # philosophy quote is the closer. (See _interview.)
        podium = s.podium[:3]
        if podium:
            turns.append(random.choice(PODIUM_HANDOFF))
            final = history[-1].standings
            for pos, name, team in podium:
                turns.extend(self._interview(name, pos, team, final, history, s))
            turns.append(("report", "Plenty to chew on -- back to you in the booth."))

        # Sign-off.
        turns.append(("pbp", f"From {s.circuit}, that's all from us. Goodnight!"))
        turns.append(("colour", random.choice([
            "Same again next week, when this lot will once more agree on absolutely nothing.",
            "Drive home safe. Unlike that lot.",
        ])))
        return turns

    # --- show helpers -------------------------------------------------------
    def _pole_read(self, d):
        """Benny's one-line read on the pole-sitter, from their stat line."""
        if d.strategy < 0.35:
            return (f"Quick as anything over one lap, {d.name} -- but the head for a race? "
                    f"We'll see. Could come back to bite.")
        if d.racecraft >= 0.78:
            return f"And {d.name} can race as well as qualify -- long afternoon for the rest, this."
        if d.tire_management >= 0.78:
            return f"{d.name} on pole AND gentle on the tyres -- track position and tyre life? That's the dream."
        return f"{d.name} starts where everyone wants to be. Now they have to keep it."

    def _watch_name(self, qualifiers):
        """A name to watch from outside the top five -- a buried strategist or a
        charger who won't stay put."""
        back = qualifiers[5:]
        if not back:
            return None
        strat = max(back, key=lambda d: d.strategy)
        if strat.strategy >= 0.7:
            return (f"And keep an eye on {strat.name}, starting {_ord(qualifiers.index(strat) + 1)} "
                    f"-- best strategic mind on this grid. Don't be surprised to see them carve through.")
        charger = max(back, key=lambda d: d.racecraft)
        if charger.racecraft >= 0.78:
            return (f"{charger.name} down in {_ord(qualifiers.index(charger) + 1)} won't last long there "
                    f"-- that one does not believe in holding position.")
        return None

    def _track_tips(self, track):
        """What to watch, generated from the track's own numbers so it stays true if
        you retune the circuit."""
        tips = []
        d = track.overtaking_difficulty
        if d >= 0.30:
            tips.append("passing here is brutal, so track position off the line is everything -- "
                        "get the start wrong and your Sunday's done")
        elif d <= 0.06:
            tips.append("they'll be streaming past all afternoon down these straights -- slipstream city")
        else:
            tips.append("a fair test for overtaking -- you can make a move stick if you're brave")
        w = track.tyre_wear
        if w >= 1.2:
            tips.append("and the tyres take an absolute hammering -- this is a strategist's race")
        elif w <= 0.6:
            tips.append("and the tyres last forever, so expect them flat out from lights to flag")
        return ("Well -- " + "; ".join(tips)
                + ". And as ever, don't get attached to the Objectivism car: "
                  "Rand and Stirner never see the flag.")

    def _podium_quote(self, name):
        pool = PODIUM_QUOTES.get(name) or PODIUM_QUOTE_FALLBACK
        return random.choice(pool) if pool else None

    # --- the podium interview -----------------------------------------------
    def _interview(self, name, pos, team, final, history, summary):
        """One driver's interview: a few RACING questions earned by what actually
        happened to them, each answered in their own voice, then the philosophy
        quote as the closer. The winner gets two angles; the others get one."""
        turns = []
        angles = self._interview_angles(name, pos, final, history, summary)
        n_blocks = 2 if pos == 1 else 1
        for angle in angles[:n_blocks]:
            turns.extend(self._interview_beats(angle, name, final))
        quote = self._podium_quote(name)              # the closer: their philosophy line
        if quote:
            key = "winner" if pos == 1 else "other"
            turns.append(("report", self._fresh(f"_closer_{key}", PODIUM_CLOSER_Q[key])))
            turns.append((name, quote))
        return turns

    def _interview_angles(self, name, pos, final, history, summary):
        """Which questions THIS driver has earned, most race-defining first. Always
        ends with a generic opener so there's never nothing to ask."""
        st = next((x for x in final if x.name == name), None)
        gained = (st.grid_position - st.position) if st else 0
        angles = []
        if pos == 1 and st and st.grid_position == 1 and summary.lead_changes == 0:
            angles.append("pole_to_win")              # led every lap from pole
        if gained >= 4:
            angles.append("charge")                   # came through the field
        mate = _TEAMMATE.get(name)
        if mate:
            mate_st = next((x for x in final if x.name == mate), None)
            if mate_st and not mate_st.retired and abs(mate_st.position - pos) <= 3:
                angles.append("teammate")             # a genuine intra-team scrap
        if any(getattr(r, "weather_change", None) for r in history):
            angles.append("weather")                  # they raced a tyre gamble
        if st and (st.damage > 0.02 or self._survived_contact(name, history)):
            angles.append("survival")                 # carried damage / survived contact
        angles.append("win_open")                     # the always-available fallback
        return angles

    def _interview_beats(self, angle, name, final):
        """The (reporter question, driver answer) turns for one angle. The teammate
        angle naturally runs two beats -- the scrap, then the team-orders follow-up."""
        if angle == "teammate":
            mate = _TEAMMATE.get(name) or "your teammate"
            q1 = self._fresh("_q_teammate", PODIUM_QUESTIONS["teammate"]).format(mate=mate)
            q2 = self._fresh("_q_team_orders", PODIUM_QUESTIONS["team_orders"])
            return [("report", q1), (name, self._answer(name, "teammate")),
                    ("report", q2), (name, self._answer(name, "team_orders"))]
        st = next((x for x in final if x.name == name), None)
        gained = max((st.grid_position - st.position) if st else 0, 0)
        start_ord = _ord(st.grid_position if st else 1)
        q = self._fresh(f"_q_{angle}", PODIUM_QUESTIONS[angle]).format(
            gained=_spell(gained), start_ord=start_ord)
        return [("report", q), (name, self._answer(name, angle))]

    def _answer(self, name, angle):
        """The driver's reply: their authored line for this angle if they have one,
        else the generic floor. Overrides get per-driver no-repeat memory; the floor
        is keyed by angle ALONE, so two finishers never echo the same floor line in
        the one ceremony."""
        override = PODIUM_ANSWERS.get(name, {}).get(angle)
        if override:
            return self._fresh(f"_ans_ovr_{name}_{angle}", override)
        pool = PODIUM_ANSWER_GENERIC.get(angle) or PODIUM_ANSWER_GENERIC["win_open"]
        return self._fresh(f"_ans_gen_{angle}", pool)

    def _survived_contact(self, name, history):
        """Was this driver in a collision they walked away from? (Sets up the
        'you took a knock and still finished' question.)"""
        for r in history:
            for inc in r.incidents:
                if inc.cause != "collision":
                    continue
                if inc.driver_name == name and not inc.retirement:
                    return True
                if inc.other_name == name and not inc.other_retired:
                    return True
        return False
