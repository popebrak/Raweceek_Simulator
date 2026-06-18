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

The marquee hook is the green-flag LULL: a lap with no events, where a real booth
fills the air with backstory and banter -- so for_lull is where the pair earns their
seats. The lap caller has ALREADY voiced the factual line by the time a Bit plays,
so an overtake Bit is the REACTION to the move, never a re-call of it.
"""

import random

from lore import (DRIVER_LORE, PAIR_LORE, TEAM_LORE, TRACK_LORE,
                  DRIVER_TRACK_LORE, GENERIC)


# Who's in the booth. Roles -> names. Change these two strings and the whole feed
# re-casts itself; add a third role here (and turns in lore.py) for a three-hander.
PERSONAS = {
    "pbp":    "Vale",     # the lap caller: excitable, plummy, sets his man up
    "colour": "Benny",    # the sidekick: ex-racer, dry, thinks the philosophy is daft
}
_TAG_WIDTH = max(len(n) for n in PERSONAS.values()) + 1   # room for the colon


def voice(lap, role, text):
    """One feed line, stamped with its speaker -- so the feed reads as a transcript.
    The speaker label is what tells the two voices apart; there's no '>>' marker."""
    tag = PERSONAS.get(role, "?").upper() + ":"
    return f"  L{lap:>2}  {tag:<{_TAG_WIDTH}} {text}"


# How often an ORDINARY pass (no authored rivalry) earns a line about the passer.
# A genuine rivalry always gets called; this keeps us from reacting to every lunge.
PLAIN_OVERTAKE_COLOUR = 0.35

# Minimum laps between two LULL fills. A real booth lets a green-flag spell breathe
# rather than narrating every quiet lap -- without this, a long procession turns
# into a back-to-back roll-call of every team. Events are unaffected; this only
# paces the backstory filler.
LULL_COOLDOWN = 4


class Booth:
    """One per race. Holds the circuit and the memory of which Bits it has used."""

    def __init__(self, track):
        self.circuit = track.circuit if track else ""
        self.used = set()
        self._last_lull_lap = -LULL_COOLDOWN       # so the first quiet lap can speak

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

    # --- event-triggered colour ---------------------------------------------
    def for_overtake(self, ov):
        """The booth's reaction to a completed pass. A real rivalry is the money
        moment and always plays; the start gets a quick character quip only for the
        drivers who have one; an ordinary pass gets a reaction only sometimes."""
        if ov.location == "the start":
            return self._pick(DRIVER_LORE.get(ov.passer, []), {"start"})
        # Directional: the lore names who passed whom, so only this ordering fits.
        gold = self._pick(PAIR_LORE.get((ov.passer, ov.passed), []), {"overtake"})
        if gold:
            return gold
        if random.random() < PLAIN_OVERTAKE_COLOUR:
            return self._pick(DRIVER_LORE.get(ov.passer, []), {"overtake", "any"})
        return None

    def for_incident(self, inc):
        """Reaction to a mistake or a retirement -- prefer the retirement-specific
        line when the car is actually out, then 'incident', then plain character."""
        pool = DRIVER_LORE.get(inc.driver_name, [])
        if inc.retirement:
            return (self._pick(pool, {"retirement"})
                    or self._pick(pool, {"incident"})
                    or self._pick(pool, {"any"}))
        return self._pick(pool, {"incident"}) or self._pick(pool, {"any"})

    # --- the green-flag lull: fill the silence ------------------------------
    def for_lull(self, standings, lap, total_laps):
        """No events this lap. After a cooldown (so we don't narrate every quiet
        lap), reach for the most specific thing available, in order: a live rivalry
        between two cars running nose-to-tail, then the leader's bond with THIS
        track, the leader's own character, a team note, the track's ghosts, and
        finally generic banter -- so there's always something, but the gold goes
        first."""
        if lap - self._last_lull_lap < LULL_COOLDOWN:
            return None                             # let the green-flag spell breathe
        running = [s for s in standings if not s.retired]

        # 1. A simmering rivalry between cars currently next to each other.
        bit = None
        for ahead, behind in zip(running, running[1:]):
            bit = self._pair_any_order(ahead.name, behind.name, {"rivalry"})
            if bit:
                break

        if bit is None and running:
            leader = running[0]
            # 2. The leader and this circuit -- the sharpest colour there is.
            pool = DRIVER_TRACK_LORE.get((leader.name, self.circuit), [])
            bit = self._pick(pool, {"leading"}) or self._pick(pool, {"any"})
            # 3. The leader's own character.
            if bit is None:
                pool = DRIVER_LORE.get(leader.name, [])
                bit = self._pick(pool, {"leading"}) or self._pick(pool, {"any"})
            # 4. A team note -- pick a running team at random for variety.
            if bit is None:
                teams = list({s.team for s in running})
                random.shuffle(teams)
                for team in teams:
                    bit = self._pick(TEAM_LORE.get(team, []), {"any"})
                    if bit:
                        break

        # 5. The track's own ghosts, then 6. generic banter.
        if bit is None:
            bit = (self._pick(TRACK_LORE.get(self.circuit, []), {"any"})
                   or self._pick(GENERIC, {"any"}))

        if bit:
            self._last_lull_lap = lap
        return bit
