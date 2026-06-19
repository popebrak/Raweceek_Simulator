"""The director -- the narrative layer that sits BETWEEN the analysis and the booth.

Until now `main.py` answered, by brute force, the question a real producer answers:
given this lap's events and everything that has happened so far, WHAT does the booth
say, in WHAT order, and HOW loud? It walked each lap's events and fired one booth
method apiece. That is perfect for "one event, one line" -- but it has no way to
build, remember, or pace. A real broadcast does all three.

The director owns that question. It is handed a lap and a running MEMORY, and it
returns an ordered list of BEATS -- sometimes empty, sometimes a crescendo. The
booth (colour.py) stays exactly what it was: the WORDS. `main.py` shrinks to "ask
the director, play the result."

THE SLICE. This first cut runs ONE event type -- overtakes -- all the way through
the new pipeline, to prove the architecture before we pour content into it. The
other event types still travel the old main->booth rails untouched; later phases
widen the seam to pull them in too. On overtakes, though, the director already does
the three things a per-event one-liner structurally cannot:

  * MEMORY -- it remembers every pass, so a fight it has seen before can be CALLED
    BACK when it flares up again ("these two AGAIN -- we saw them scrapping earlier").
  * DEVELOPMENT -- a battle is tracked as an ARC with a life of its own (opened ->
    traded -> went quiet -> reignited), not a one-shot line fired and forgotten.
  * PACING -- each lap has an ATTENTION BUDGET. Candidate passes are scored by
    salience, the most important are kept, the rest are still REMEMBERED (so the
    order stays truthful and a later callback can lean on them) but not spoken. A
    busy lap calls the two passes that matter instead of machine-gunning all five.

A NOTE ON THE SEAM WITH THE BOOTH. colour.py already keeps a small `_battles` dict
to smooth the PHRASING of cars trading a place ("...and back through!"). That is a
baby version of arc-tracking living in the wrong layer -- the kind of reasoning the
director exists to own. For this slice we leave it where it is: it does no harm and
keeps the trading phrasing tidy, while the REAL narrative memory (callbacks, pacing)
lives here. Folding the booth's version up into the director is a clean follow-up,
not a prerequisite.
"""

from dataclasses import dataclass, field


# --- What's worth calling ----------------------------------------------------
# Moved here from main.py: deciding WHICH passes make the broadcast is a narrative
# judgement, so it belongs to the director, not the playback loop. F1 scores the top
# ten, so a pass for the points or better is the story; deeper midfield churn isn't.
NOTABLE_OVERTAKE = 3      # baseline: call passes for this position or better; hard tracks widen it
POINTS_POSITIONS = 10     # passes below this rarely matter -- the points are the story
START_JUMP_WORTH = 3      # a launch this big gets called even from outside the points

# --- Pacing ------------------------------------------------------------------
# The attention budget: how many overtake BEATS the booth will actually voice in a
# single lap. The start is the one moment a real booth rattles through several
# getaways, so it gets a wider budget; a normal racing lap is kept tight, which is
# what makes the director DROP the third midfield pass and call the fight up front.
OVERTAKE_BUDGET = 2       # spoken overtake beats on a green-flag racing lap
START_BUDGET = 4          # ...and on the opening lap, where a flurry is realistic

# --- Memory ------------------------------------------------------------------
# A battle that has gone quiet for longer than this many laps is no longer "ongoing".
# If the same two cars start trading again after such a lull, that is a REIGNITION --
# a fight the booth remembers and calls back, not just another swap. Deliberately
# wider than colour.BATTLE_WINDOW (which governs phrasing), so a callback only fires
# when the gap is long enough that "and again!" really would be a lie.
REIGNITE_GAP = 5

# --- Salience ----------------------------------------------------------------
# How loudly a pass clamours for the booth's attention. Position is the spine of it
# (the lead is always the story); a developing scrap climbs the running order as it
# escalates; a fight flaring back up after a lull is itself an event.
SALIENCE_BY_POSITION = {"lead": 100, "podium": 60, "points": 30, "midfield": 10}
SALIENCE_PER_EXCHANGE = 8     # each trade of the place pushes a battle further up the bill
SALIENCE_REIGNITION = 25      # a remembered fight coming back to life
SALIENCE_PER_GAINED = 6       # a big launch off the line earns its call


@dataclass
class Beat:
    """One unit the director emits. `turns` is a list of (role, line) pairs, exactly
    like a lore Bit -- so main.py's existing `play()` plays a Beat with no changes.
    `intensity` and `kind` are the director's own metadata (the pacing engine and,
    later, the audio layer can lean on them); the booth never sees them."""
    turns: tuple
    intensity: int = 1
    kind: str = "overtake"


@dataclass
class BattleArc:
    """A developing fight over one position, tracked across laps. This is the unit
    of DEVELOPMENT: the director checks back in on it rather than re-deriving a fresh
    line every time the place changes hands."""
    pair: frozenset
    position: int            # the place being contested (kept current as it moves)
    opened_lap: int
    last_lap: int            # the most recent lap these two traded
    leader: str = ""         # who is currently ahead, of the two
    exchanges: int = 0       # how many times the place has swapped since opening
    reignitions: int = 0     # how many times it has flared back up after going quiet
    called_back: int = 0     # how many reignition callbacks have actually been voiced


class RaceMemory:
    """Everything the director knows so far about THIS race -- the substrate memory
    and callbacks read from.

    THE BOUNDARY THAT MATTERS. This is deliberately a per-RACE object with a clean
    edge. When the season layer arrives, a SeasonMemory will WRAP one of these per
    round and add the only thing a single race can't know -- standings, title stakes,
    'a must-not-finish for Rand's perfect record'. Championship colour is just
    season-spanning memory, so if we keep this seam honest now, the two never need
    reworking later. Nothing in here reaches outside the race; nothing outside reaches
    in except through this object.
    """

    def __init__(self):
        self.arcs = {}            # frozenset(pair) -> BattleArc
        self.passes = []          # every pass the director was shown, in order (the truthful log)
        self.spoken = 0           # how many overtake beats were actually voiced (for pacing stats)

    def arc_for(self, pair):
        return self.arcs.get(pair)

    def open_arc(self, pair, position, lap, leader):
        arc = BattleArc(pair=pair, position=position, opened_lap=lap,
                        last_lap=lap, leader=leader)
        self.arcs[pair] = arc
        return arc

    def log_pass(self, ov):
        self.passes.append((ov.lap, ov.passer, ov.passed, ov.position))


class Director:
    """One per race. Wraps the booth (for words) and a RaceMemory (for continuity),
    and turns a lap's events into an ordered, paced list of Beats. For the slice it
    handles overtakes; everything else still flows through main.py's old path."""

    def __init__(self, track, booth, memory=None):
        self.track = track
        self.booth = booth
        self.memory = memory or RaceMemory()
        # Where passing is hard (Monaco, Suzuka) even a midfield move is an event, so
        # we call deeper into the field; where it's cheap (Monza) we keep it to the
        # sharp end. Same rule the old main.py used, now owned by the narrative layer.
        self.notable_pos = NOTABLE_OVERTAKE
        if track is not None:
            self.notable_pos += round(track.overtaking_difficulty * 10)

    # --- worth calling -------------------------------------------------------
    def _worth(self, ov):
        """Does this pass make the broadcast? The lead and podium always; elsewhere it
        has to be for a points place -- or, off the line, a genuine flier."""
        if ov.location == "the start":
            return ov.position <= POINTS_POSITIONS or ov.places_gained >= START_JUMP_WORTH
        return ov.position <= min(self.notable_pos, POINTS_POSITIONS)

    def _position_band(self, position):
        if position == 1:
            return "lead"
        if position <= 3:
            return "podium"
        if position <= POINTS_POSITIONS:
            return "points"
        return "midfield"

    # --- the slice: narrate a lap's overtakes --------------------------------
    def overtakes(self, report):
        """The wired vertical slice. Read this lap's passes, update the battle arcs,
        score every candidate by salience, keep the most important up to the lap's
        budget, and return them as ordered Beats. Dropped passes are still logged in
        memory, so the race's story stays truthful even when the booth stays quiet."""
        lap = report.lap
        candidates = []   # (salience, ov, arc, reignited)

        for ov in report.overtakes:
            self.memory.log_pass(ov)
            if not self._worth(ov):
                continue

            reignited = False
            arc = None
            # The start is a launch, not a scrap -- it opens no arc, but it still
            # competes for the lap's budget like any other call.
            if ov.location != "the start":
                pair = frozenset((ov.passer, ov.passed))
                arc = self.memory.arc_for(pair)
                if arc is None:
                    arc = self.memory.open_arc(pair, ov.position, lap, ov.passer)
                elif lap - arc.last_lap > REIGNITE_GAP and arc.exchanges >= 1:
                    # Gone quiet, now back: a remembered fight, not just another swap.
                    reignited = True
                    arc.reignitions += 1
                    arc.last_lap, arc.position, arc.leader = lap, ov.position, ov.passer
                else:
                    arc.exchanges += 1
                    arc.last_lap, arc.position, arc.leader = lap, ov.position, ov.passer

            candidates.append((self._salience(ov, arc, reignited), ov, arc, reignited))

        if not candidates:
            return []

        # PACING. Loudest first, then keep only what the lap's attention budget allows.
        candidates.sort(key=lambda c: c[0], reverse=True)
        budget = START_BUDGET if lap == 1 else OVERTAKE_BUDGET
        kept = candidates[:budget]

        beats = []
        for salience, ov, arc, reignited in kept:
            beats.append(self._build_beat(ov, arc, reignited, lap, salience))
        self.memory.spoken += len(beats)
        return beats

    def _salience(self, ov, arc, reignited):
        score = SALIENCE_BY_POSITION[self._position_band(ov.position)]
        if ov.location == "the start":
            score += SALIENCE_PER_GAINED * ov.places_gained
        if arc is not None:
            score += SALIENCE_PER_EXCHANGE * arc.exchanges
        if reignited:
            score += SALIENCE_REIGNITION
        return score

    def _build_beat(self, ov, arc, reignited, lap, salience):
        """Assemble the actual turns for one kept pass, asking the booth for every
        word. A reignition leads with a callback line -- the memory made audible --
        before the normal call; otherwise it's the standard call plus, sometimes, the
        booth's colour. Intensity rides with salience so a future audio layer (and the
        pacing of the run-in) has a loudness to read."""
        turns = []
        if reignited and arc is not None and arc.called_back < 1:
            laps_since = lap - arc.opened_lap
            turns.append(("pbp", self.booth.call_battle_callback(ov, laps_since)))
            arc.called_back += 1

        turns.append(("pbp", self.booth.call_overtake(ov, lap)))

        colour = self.booth.for_overtake(ov)   # the history behind the move, when there is one
        if colour:
            turns.extend(colour.turns)

        intensity = 3 if salience >= 80 else 2 if salience >= 40 else 1
        return Beat(turns=tuple(turns), intensity=intensity, kind="overtake")
