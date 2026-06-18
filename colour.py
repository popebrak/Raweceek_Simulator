"""The colour analyst -- the SECOND voice in the booth.

display.render_* is the lap caller: it says WHAT just happened (a pass, a crash, a
stop). This module is the colour analyst beside them, saying what it MEANS -- the
history between two drivers, a team's character, a track's ghosts.

It is a second consumer of the very same event stream the lap caller reads -- an
Overtake, an Incident, the running order. Given a moment it reaches into lore.py
for a line that fits, prefers the rare relational gold (Nietzsche on Plato) over
generic filler, and remembers what it has already said so it never repeats itself
in a race.

The quietest, most important hook is the green-flag LULL: a lap with no events at
all, where main.py would otherwise sit in silence. That is exactly where a real
booth fills the air with backstory -- so for_lull is where the analyst earns its
seat. The selection is a PRIORITY policy (specific gold first, generic last), the
same shape as the "is this pass even worth calling?" threshold already in display.
"""

import random

from lore import (DRIVER_LORE, PAIR_LORE, TEAM_LORE, TRACK_LORE,
                  DRIVER_TRACK_LORE, GENERIC)


# How often an ORDINARY pass (no authored rivalry) earns a line about the passer.
# Genuine rivalries always get called; this keeps us from editorialising every
# single midfield lunge into a history lecture.
PLAIN_OVERTAKE_COLOUR = 0.3


class ColourCommentator:
    """One per race. Holds the circuit and the memory of what's been said."""

    def __init__(self, track):
        self.circuit = track.circuit if track else ""
        self.used = set()

    def _pick(self, candidates, tags):
        """From a pool of Colour, keep those whose trigger is in `tags` and that we
        haven't used yet, then choose one (weighted). Mark it used; return its text,
        or None if the pool is dry. Marking-on-use is what guarantees no repeats."""
        pool = [c for c in candidates if c.when in tags and c.line not in self.used]
        if not pool:
            return None
        chosen = random.choices(pool, weights=[c.weight for c in pool])[0]
        self.used.add(chosen.line)
        return chosen.line

    def _pair_any_order(self, a, b, tags):
        """Pair lore that reads either way (a rivalry) -- try both orderings."""
        return (self._pick(PAIR_LORE.get((a, b), []), tags)
                or self._pick(PAIR_LORE.get((b, a), []), tags))

    # --- event-triggered colour ---------------------------------------------
    def for_overtake(self, ov):
        """The history behind a completed pass. A real rivalry is the money moment
        and always gets called; an ordinary pass gets the passer's character only
        sometimes, so the good lines stay special."""
        if ov.location == "the start":
            pool = DRIVER_LORE.get(ov.passer, [])
            return self._pick(pool, {"start"}) or self._pick(pool, {"any"})

        # Directional: the line names who passed whom, so only this ordering fits.
        gold = self._pick(PAIR_LORE.get((ov.passer, ov.passed), []), {"overtake"})
        if gold:
            return gold

        if random.random() < PLAIN_OVERTAKE_COLOUR:
            pool = DRIVER_LORE.get(ov.passer, [])
            return self._pick(pool, {"overtake"}) or self._pick(pool, {"any"})
        return None

    def for_incident(self, inc):
        """A mistake or a retirement -- prefer a retirement-specific line when the
        car is actually out, falling back through 'incident' to plain character."""
        pool = DRIVER_LORE.get(inc.driver_name, [])
        if inc.retirement:
            return (self._pick(pool, {"retirement"})
                    or self._pick(pool, {"incident"})
                    or self._pick(pool, {"any"}))
        return self._pick(pool, {"incident"}) or self._pick(pool, {"any"})

    # --- the green-flag lull: fill the silence ------------------------------
    def for_lull(self, standings, lap, total_laps):
        """No events this lap. Reach for the most specific colour available, in
        order: a live rivalry between two cars running nose-to-tail, then the
        leader's bond with THIS track, the leader's own character, a team note,
        the track's history, and finally generic filler -- so there is always a
        line, but the specific gold gets first refusal."""
        running = [s for s in standings if not s.retired]

        # 1. A simmering rivalry between cars currently next to each other.
        for ahead, behind in zip(running, running[1:]):
            line = self._pair_any_order(ahead.name, behind.name, {"rivalry"})
            if line:
                return line

        if running:
            leader = running[0]
            # 2. The leader and this circuit -- the sharpest colour there is.
            pool = DRIVER_TRACK_LORE.get((leader.name, self.circuit), [])
            line = self._pick(pool, {"leading"}) or self._pick(pool, {"any"})
            if line:
                return line
            # 3. The leader's own character.
            pool = DRIVER_LORE.get(leader.name, [])
            line = self._pick(pool, {"leading"}) or self._pick(pool, {"any"})
            if line:
                return line
            # 4. A team note -- pick a running team at random for variety.
            teams = list({s.team for s in running})
            random.shuffle(teams)
            for team in teams:
                line = self._pick(TEAM_LORE.get(team, []), {"any"})
                if line:
                    return line

        # 5. The track's own ghosts, then 6. generic filler.
        return (self._pick(TRACK_LORE.get(self.circuit, []), {"any"})
                or self._pick(GENERIC, {"any"}))
