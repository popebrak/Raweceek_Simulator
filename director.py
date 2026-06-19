"""The director -- the narrative layer that sits BETWEEN the analysis and the booth.

`main.py` used to answer, by brute force, the question a real producer answers: given
this lap's events and everything that's happened so far, WHAT does the booth say, in
WHAT order, and HOW loud? It walked each lap's events and fired one booth method
apiece. That's fine for "one event, one line" -- but it can't build, remember, or
pace, and a real broadcast does all three.

The director owns that question now. It's handed a lap and a running MEMORY, and it
returns an ordered list of BEATS -- sometimes empty, sometimes a crescendo. The booth
(colour.py) stays exactly what it was: the WORDS. `main.py` shrinks to "ask the
director, play the result" (plus the two structural bookends -- lights-out and the
flag -- and the quiet-lap chatter).

THE PRODUCER'S DESK. Every event type -- weather, incidents, the stewards, passes,
pit stops and undercuts -- is turned into CANDIDATES: a beat, a SALIENCE (how loudly
it clamours for the air), and whether it's MANDATORY. The desk then does what a real
producer does on a busy lap:

  * MEMORY -- it remembers every pass, so a fight it has seen before can be CALLED
    BACK when it flares up again, and a crash or an undercut can be recognised as the
    END of a battle it's been following (arcs span event types).
  * DEVELOPMENT -- a fight is a BattleArc with a life of its own (opened -> traded ->
    went quiet -> reignited -> resolved by a pass, a crash, an undercut, or a DNF).
  * PACING -- ONE shared airtime budget per lap. The MANDATORY tier (a retirement,
    the lead changing hands, contact, a verdict, an undercut, a weather call) is never
    dropped; everything else competes on salience for the lap's remaining slots. The
    losers are still REMEMBERED (the order stays truthful, callbacks still land), just
    not voiced. A frantic lap calls the three biggest stories instead of machine-
    gunning all nine; a quiet lap lets a minor lock-up through because there's room.

A NOTE ON THE SEAM WITH THE BOOTH. colour.py still keeps a small `_battles` dict to
smooth the PHRASING of cars trading a place. That's a baby arc-tracker living in the
phrasing layer; the REAL narrative memory lives here. Folding the booth's version up
into the director is a clean future tidy, not a prerequisite.

WHAT'S STILL TO COME. The per-lap `observe()` hook (it watches the timing tower for
pursuits) is also where a future neutralisation phase -- safety car, VSC, red flag --
will read the field to pace a restart. And the structural bookends (lights-out, the
finish) stay in main.py for now because they must lead and trail no matter what.
"""

from dataclasses import dataclass
import random


# --- What's worth calling ----------------------------------------------------
# Deciding WHICH passes make the broadcast is a narrative judgement, so it lives here.
# F1 scores the top ten, so a pass for the points or better is the story.
NOTABLE_OVERTAKE = 3      # baseline: call passes for this position or better; hard tracks widen it
POINTS_POSITIONS = 10     # passes below this rarely matter -- the points are the story
START_JUMP_WORTH = 3      # a launch this big gets called even from outside the points

# --- Pacing: the shared airtime budget ---------------------------------------
# The one knob that governs feed DENSITY. Mandatory beats (see below) always play;
# OPTIONAL beats compete for this many slots per lap. The start is the one moment a
# booth rattles through several getaways, so it gets a wider budget. Turn LAP_BUDGET
# up for a chattier feed, down for a sparser, pick-your-moments one.
LAP_BUDGET = 3            # optional beats voiced on a normal racing lap
START_BUDGET = 4          # ...and on the opening lap, where a flurry of getaways is realistic

# --- The rundown -------------------------------------------------------------
# How often the booth recaps the running order on a quiet lap, and how far from the
# flag to stop (the closing laps belong to the run-in, which builds its own tension).
RUNDOWN_MIN_GAP = 9       # laps between order readouts
RUNDOWN_SKIP_FINAL = 6    # leave the closing laps to the run-in

# --- Memory ------------------------------------------------------------------
# A battle quiet for longer than this is no longer "ongoing"; if the pair start
# trading again after such a lull, that's a REIGNITION the booth calls back. Wider
# than colour.BATTLE_WINDOW (phrasing) so a callback only fires when "and again!"
# really would be a lie.
REIGNITE_GAP = 5

# A fight counts as 'current' -- live enough to be RESOLVED by a crash or undercut and
# have that named as its end -- only if it was active within this window.
ARC_LIVE_WINDOW = REIGNITE_GAP

# PURSUIT: a fight with no completed pass. Two cars locked nose-to-tail, lap after lap,
# is a battle even though nobody's got by -- and it's what lets an undercut (or a late
# crash) settle a fight the cars couldn't win on track. Inferred from the timing tower.
PURSUIT_GAP = 1.2          # seconds to the car ahead that count as 'stuck behind'
PURSUIT_MIN_LAPS = 3       # consecutive close laps before it's a genuine fight

# --- Incident worth (the cheap pre-gate, before the budget) ------------------
# Race-changing incidents are always candidates; these two dials decide whether a
# merely scruffy moment is even WORTH considering (it then still competes for airtime).
MODERATE_INCIDENT_CALL = 0.5     # a real wobble, time lost: considered about half the time
MINOR_INCIDENT_CALL = 0.12       # a harmless off: mostly not even considered

# --- Pits --------------------------------------------------------------------
PIT_CALL_POSITION = 6      # only the sharp end's stops are worth considering at all

# --- Salience: one scale across every event type -----------------------------
# This is what lets a crash, a pass, and a pit stop be weighed against each other on
# the same desk. Position is the spine of a pass (the lead is always the story); the
# event kinds slot in around it. Mandatory beats also carry a salience -- it sets their
# ORDER in the feed (the biggest story spoken first), even though they're never cut.
SALIENCE_BY_POSITION = {"lead": 100, "podium": 60, "points": 30, "midfield": 10}
SALIENCE_PER_EXCHANGE = 8     # each trade of a place pushes a battle further up the bill
SALIENCE_REIGNITION = 25      # a remembered fight coming back to life
SALIENCE_PER_GAINED = 6       # a big launch off the line earns its call

SAL_WEATHER = 120             # a weather call is the headline -- it leads the lap
SAL_SAFETY_CAR = 130          # ...and a safety car is a bigger one still -- it leads everything
SAL_RESTART = 110             # the green-flag restart -- a crescendo above the racing
SAL_RETIREMENT = 90           # someone's race is over
SAL_BATTLE_CONTACT = 85       # a tracked fight ends in contact
SAL_UNDERCUT_SETTLE = 80      # an undercut settles a fight they couldn't win on track
SAL_COLLISION = 70            # contact, survived
SAL_UNDERCUT = 70             # a plain undercut -- still the strategic story
SAL_PENALTY_VERDICT = 65      # the stewards hand down a (non-warning) verdict
SAL_MAJOR_INCIDENT = 60       # a big solo moment, survived
SAL_PENALTY_SERVED = 60       # a drive-through / stop-go being taken, now
SAL_PIT_SHARP = 45            # a sharp-end (podium) stop
SAL_MODERATE_INCIDENT = 40    # a scruffy-but-survived wobble
SAL_PIT = 30                  # a points-end stop
SAL_INVESTIGATION = 25        # "under investigation" -- the suspense beat
SAL_PENALTY_WARNING = 15      # a black-and-white warning -- minor
SAL_MINOR_INCIDENT = 15       # a harmless off


@dataclass
class Beat:
    """One unit the director emits. `turns` is a list of (role, line) pairs, exactly
    like a lore Bit -- so main.py's existing `play()` plays a Beat with no changes.
    `intensity` and `kind` are the director's own metadata (a future audio layer can
    lean on them); the booth never sees them."""
    turns: tuple
    intensity: int = 1
    kind: str = "overtake"


@dataclass
class Candidate:
    """A beat competing for the lap's airtime. `salience` is its priority on the one
    cross-type scale; `mandatory` beats are never cut, only ordered."""
    beat: Beat
    salience: float
    mandatory: bool = False


@dataclass
class BattleArc:
    """A developing fight over one position, tracked across laps. The unit of
    DEVELOPMENT: the director checks back in on it rather than re-deriving a fresh
    line every time the place changes hands."""
    pair: frozenset
    position: int            # the place being contested (kept current as it moves)
    opened_lap: int
    last_lap: int            # the most recent lap these two traded
    leader: str = ""         # who is currently ahead, of the two
    exchanges: int = 0       # how many times the place has swapped since opening
    reignitions: int = 0     # how many times it has flared back up after going quiet
    called_back: int = 0     # how many reignition callbacks have actually been voiced
    pursuit: bool = False    # armed by close running even with no pass completed
    resolved: str = ""       # "" while live; else how it ENDED: contact|undercut|retirement


class RaceMemory:
    """Everything the director knows so far about THIS race -- the substrate memory
    and callbacks read from.

    THE BOUNDARY THAT MATTERS. This is deliberately a per-RACE object with a clean
    edge. When the season layer arrives, a SeasonMemory will WRAP one of these per
    round and add the only thing a single race can't know -- standings, title stakes,
    'a must-not-finish for Rand's perfect record'. Championship colour is just
    season-spanning memory, so if we keep this seam honest now, the two never need
    reworking. Nothing in here reaches outside the race; nothing reaches in except
    through this object.
    """

    def __init__(self):
        self.arcs = {}            # frozenset(pair) -> BattleArc
        self.pursuit = {}         # frozenset(pair) -> consecutive close-running laps (the streak)
        self.passes = []          # every pass the director was shown, in order (the truthful log)
        self.spoken = 0           # total beats actually voiced (for pacing stats)
        self.last_rundown_lap = 0 # the lap of the most recent state-of-the-race readout

    def arc_for(self, pair):
        return self.arcs.get(pair)

    def open_arc(self, pair, position, lap, leader):
        arc = BattleArc(pair=pair, position=position, opened_lap=lap,
                        last_lap=lap, leader=leader)
        self.arcs[pair] = arc
        return arc

    def close_arcs_for(self, name, reason):
        """Settle every live arc this driver is part of -- a retirement ends the fight.
        Stops a dead driver's battle lingering to be reignited or resolved later."""
        for arc in self.arcs.values():
            if not arc.resolved and name in arc.pair:
                arc.resolved = reason

    def log_pass(self, ov):
        self.passes.append((ov.lap, ov.passer, ov.passed, ov.position))


class Director:
    """One per race. Wraps the booth (for words) and a RaceMemory (for continuity),
    and turns a lap's events into an ordered, paced list of Beats via narrate()."""

    def __init__(self, track, booth, memory=None):
        self.track = track
        self.booth = booth
        self.memory = memory or RaceMemory()
        # Where passing is hard (Monaco, Suzuka) even a midfield move is an event, so
        # we call deeper into the field; where it's cheap (Monza) we keep it tight.
        self.notable_pos = NOTABLE_OVERTAKE
        if track is not None:
            self.notable_pos += round(track.overtaking_difficulty * 10)

    # =========================================================================
    # THE DESK: gather every candidate, then pace them to one shared budget.
    # =========================================================================
    def narrate(self, report, telemetry=False):
        """The producer's desk. Gather candidate beats from every event type on this
        lap, then voice the mandatory tier plus the most salient optional beats the
        lap's airtime budget allows -- biggest story first.

        Gathering ORDER matters (it drives the arc bookkeeping): pursuits are observed
        first, then incidents resolve fight-ending CONTACT, then passes update the
        arcs, then undercuts resolve fights won in the pits. The SPOKEN order is then
        re-sorted by salience, independent of the bookkeeping order.

        Under a NEUTRALISATION there is no racing: a crawling lap produces only the
        deploy headline and the cheap-stop scramble, and we don't observe pursuits (a
        bunched, parked field isn't a fight). The restart lap is green again, so the
        full machinery resumes -- and the bunched field it inherits feeds the pursuit
        arcs all on its own."""
        caution = getattr(report, "caution", None)
        if caution is not None and caution.status in ("deploy", "running"):
            cands = self._caution_candidates(report)
            cands += self._pit_candidates(report)        # the cheap-stop rush still calls
            return self._assemble(cands, report.lap)

        self.observe(report)
        cands = self._caution_candidates(report)         # the restart crescendo, if this is one
        cands += self._weather_candidates(report)
        cands += self._incident_candidates(report, telemetry)
        cands += self._steward_candidates(report)
        cands += self._overtake_candidates(report)
        cands += self._pit_candidates(report)
        return self._assemble(cands, report.lap)

    def _caution_candidates(self, report):
        """The safety car as commentary: the deployment is the loudest headline on the
        board, the restart a crescendo back to green. The crawl laps in between say
        nothing here (the booth fills them from the quiet-lap path)."""
        c = getattr(report, "caution", None)
        if c is None:
            return []
        if c.status == "deploy":
            beat = Beat(tuple(self.booth.call_safety_car(c).turns), 3, "caution")
            return [Candidate(beat, SAL_SAFETY_CAR, mandatory=True)]
        if c.status == "restart":
            beat = Beat(tuple(self.booth.call_restart(c).turns), 3, "caution")
            return [Candidate(beat, SAL_RESTART, mandatory=True)]
        return []

    def _assemble(self, cands, lap):
        """Mandatory beats always make it; optional beats compete for the budget. Then
        everything kept is ordered loudest-first so the lap leads with its big story."""
        mandatory = [c for c in cands if c.mandatory]
        optional = sorted((c for c in cands if not c.mandatory),
                          key=lambda c: c.salience, reverse=True)
        budget = START_BUDGET if lap == 1 else LAP_BUDGET
        kept = mandatory + optional[:budget]
        kept.sort(key=lambda c: c.salience, reverse=True)
        self.memory.spoken += len(kept)
        return [c.beat for c in kept]

    def rundown(self, report, total_laps):
        """A periodic 'state of the race' readout for a QUIET lap (main reaches for it
        before the philosophy chatter). The booth recaps the order so a listener knows
        where everyone stands. Cadence is the director's call -- not too often, not on
        lap one, and never in the closing laps (those belong to the run-in). Returns a
        Beat or None. The WORDS, and their variety, are the booth's job (call_rundown)."""
        lap = report.lap
        if lap <= 1 or total_laps - lap < RUNDOWN_SKIP_FINAL:
            return None
        if lap - self.memory.last_rundown_lap < RUNDOWN_MIN_GAP:
            return None
        if sum(1 for s in report.standings if not s.retired) < 4:
            return None
        bit = self.booth.call_rundown(report.standings, lap, total_laps)
        if not bit:
            return None
        self.memory.last_rundown_lap = lap
        return Beat(tuple(bit.turns), intensity=1, kind="rundown")

    # --- helpers -------------------------------------------------------------
    def _worth(self, ov):
        """Does this pass make the broadcast at all? The lead and podium always;
        elsewhere it has to be for a points place -- or, off the line, a genuine flier."""
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

    def _salience(self, ov, arc, reignited):
        score = SALIENCE_BY_POSITION[self._position_band(ov.position)]
        if ov.location == "the start":
            score += SALIENCE_PER_GAINED * ov.places_gained
        if arc is not None:
            score += SALIENCE_PER_EXCHANGE * arc.exchanges
        if reignited:
            score += SALIENCE_REIGNITION
        return score

    # --- weather -------------------------------------------------------------
    def _weather_candidates(self, report):
        """A change in the weather is the headline -- it sets up the spins and the dive
        for the pit lane that follow, so it leads the lap (top salience, mandatory)."""
        change = getattr(report, "weather_change", "")
        if not change:
            return []
        bit = self.booth.for_weather(change)
        if not bit:
            return []
        beat = Beat(tuple(bit.turns), intensity=3, kind="weather")
        return [Candidate(beat, SAL_WEATHER, mandatory=True)]

    # --- incidents -----------------------------------------------------------
    def _incident_worth(self, inc):
        """Is this incident even worth considering? Race-changing ones always are; a
        scruffy moment about half the time; a harmless off, rarely. (Those that pass
        still compete for airtime against everything else on the lap.)"""
        if inc.retirement or inc.other_retired:
            return True
        if inc.cause == "collision":
            return True
        if inc.severity == "major":
            return True
        if inc.severity == "moderate":
            return random.random() < MODERATE_INCIDENT_CALL
        return random.random() < MINOR_INCIDENT_CALL

    def _incident_candidates(self, report, telemetry=False):
        """The cross-type win lives here: a collision between two cars the director has
        been watching FIGHT is called as the climax of that battle (a lead-in before
        the mechanical collision call), and the arc is settled. Any retirement also
        closes the arcs of whoever's out, even if the moment itself isn't voiced."""
        cands = []
        for inc in report.incidents:
            framed = False
            if inc.cause == "collision" and inc.other_name:
                arc = self._live_arc(frozenset((inc.driver_name, inc.other_name)), report.lap)
                if arc is not None:
                    arc.resolved = "contact"
                    framed = True

            if not self._incident_worth(inc):
                self._close_on_retire(inc)        # settle arcs even when we don't voice it
                continue

            turns = []
            if framed:
                turns.append(("pbp", self.booth.call_battle_contact(inc)))
            turns.append(("pbp", self.booth.call_incident(inc)))
            if telemetry:
                # Debug-only annotation. Imported locally so the narrative director
                # carries no module-level dependency on the rendering layer.
                from display import render_telemetry
                tele = render_telemetry(inc).strip()
                if tele:
                    turns.append((None, f"        {tele}"))
            colour = self.booth.for_incident(inc)
            if colour:
                turns.extend(colour.turns)

            out = inc.retirement or inc.other_retired
            if out:
                sal, mand, inten = SAL_RETIREMENT, True, 3
            elif framed:
                sal, mand, inten = SAL_BATTLE_CONTACT, True, 3
            elif inc.cause == "collision":
                sal, mand, inten = SAL_COLLISION, True, 2
            elif inc.severity == "major":
                sal, mand, inten = SAL_MAJOR_INCIDENT, True, 2
            elif inc.severity == "moderate":
                sal, mand, inten = SAL_MODERATE_INCIDENT, False, 2
            else:
                sal, mand, inten = SAL_MINOR_INCIDENT, False, 1

            cands.append(Candidate(Beat(tuple(turns), inten, "incident"), sal, mand))
            self._close_on_retire(inc)
        return cands

    def _close_on_retire(self, inc):
        if inc.retirement:
            self.memory.close_arcs_for(inc.driver_name, "retirement")
        if inc.other_retired:
            self.memory.close_arcs_for(inc.other_name, "retirement")

    # --- the stewards --------------------------------------------------------
    def _steward_candidates(self, report):
        """Investigations and verdicts. The 'under investigation' note is a skippable
        suspense beat; a non-warning verdict (or a drive-through being served) is news
        and never cut; a black-and-white warning is minor and competes like the rest."""
        cands = []
        for inv in report.investigations:
            beat = Beat((("pbp", self.booth.call_investigation(inv)),), 1, "steward")
            cands.append(Candidate(beat, SAL_INVESTIGATION, mandatory=False))
        for pen in report.penalties:
            if pen.served:
                beat = Beat((("pbp", self.booth.call_penalty_served(pen)),), 2, "steward")
                cands.append(Candidate(beat, SAL_PENALTY_SERVED, mandatory=True))
                continue
            turns = [("pbp", self.booth.call_penalty(pen))]
            colour = self.booth.for_penalty(pen)
            if colour:
                turns.extend(colour.turns)
            if pen.kind == "warning":
                cands.append(Candidate(Beat(tuple(turns), 1, "steward"),
                                       SAL_PENALTY_WARNING, mandatory=False))
            else:
                cands.append(Candidate(Beat(tuple(turns), 2, "steward"),
                                       SAL_PENALTY_VERDICT, mandatory=True))
        return cands

    # --- overtakes -----------------------------------------------------------
    def _overtake_candidates(self, report):
        """Read the lap's passes, update the battle arcs, and produce a candidate for
        each pass worth calling. The lead changing hands is mandatory; everything else
        competes. EVERY pass is logged to memory first, worthy or not, so the race's
        story stays truthful even when the booth stays quiet."""
        lap = report.lap
        cands = []
        for ov in report.overtakes:
            self.memory.log_pass(ov)
            if not self._worth(ov):
                continue

            reignited = False
            arc = None
            if ov.location != "the start":     # a launch is no scrap -- it opens no arc
                pair = frozenset((ov.passer, ov.passed))
                arc = self.memory.arc_for(pair)
                if arc is None or arc.resolved:
                    arc = self.memory.open_arc(pair, ov.position, lap, ov.passer)
                elif lap - arc.last_lap > REIGNITE_GAP and arc.exchanges >= 1:
                    reignited = True
                    arc.reignitions += 1
                    arc.last_lap, arc.position, arc.leader = lap, ov.position, ov.passer
                else:
                    # ongoing scrap -- including the first pass that breaks a PURSUIT arc
                    arc.exchanges += 1
                    arc.pursuit = False
                    arc.last_lap, arc.position, arc.leader = lap, ov.position, ov.passer

            salience = self._salience(ov, arc, reignited)
            beat = self._build_overtake_beat(ov, arc, reignited, lap, salience)
            cands.append(Candidate(beat, salience, mandatory=(ov.position == 1)))
        return cands

    def _build_overtake_beat(self, ov, arc, reignited, lap, salience):
        """Assemble the turns for one pass, asking the booth for every word. A
        reignition leads with a callback line -- the memory made audible."""
        turns = []
        if reignited and arc is not None and arc.called_back < 1:
            laps_since = lap - arc.opened_lap
            turns.append(("pbp", self.booth.call_battle_callback(ov, laps_since)))
            arc.called_back += 1
        turns.append(("pbp", self.booth.call_overtake(ov, lap)))
        colour = self.booth.for_overtake(ov)
        if colour:
            turns.extend(colour.turns)
        intensity = 3 if salience >= 80 else 2 if salience >= 40 else 1
        return Beat(tuple(turns), intensity, "overtake")

    # --- pits & undercuts ----------------------------------------------------
    def _pit_candidates(self, report):
        """Sharp-end stops get a call; an undercut is always the strategic story -- and
        when it lands on a rival the cars have been fighting, it's called as the fight
        settled in the pit lane, and the arc is resolved."""
        pos_of = {s.name: s.position for s in report.standings}
        cands = []
        for ps in report.pit_stops:
            pos = pos_of.get(ps.driver_name, 99)
            if pos <= PIT_CALL_POSITION:
                turns = [("pbp", self.booth.call_pit(ps))]
                colour = self.booth.for_pit(ps)   # the desk decides IF; the booth, WHAT
                if colour:
                    turns.extend(colour.turns)
                sal = SAL_PIT_SHARP if pos <= 3 else SAL_PIT
                cands.append(Candidate(Beat(tuple(turns), 1, "pit"), sal, mandatory=False))

        for uc in report.undercuts:
            arc = self._live_arc(frozenset((uc.undercutter, uc.victim)), report.lap)
            if arc is not None:
                arc.resolved = "undercut"
                arc.leader = uc.undercutter       # the winner ends ahead -- the debrief reads this
                beat = Beat((("pbp", self.booth.call_battle_undercut(uc)),), 3, "undercut")
                cands.append(Candidate(beat, SAL_UNDERCUT_SETTLE, mandatory=True))
            else:
                beat = Beat((("pbp", self.booth.call_undercut(uc)),), 2, "undercut")
                cands.append(Candidate(beat, SAL_UNDERCUT, mandatory=True))
        return cands

    # --- pursuit: a fight with no completed pass -----------------------------
    def observe(self, report):
        """Run EVERY lap, event or not. Watch the timing tower for cars locked nose to
        tail -- a small gap held lap after lap -- and arm a PURSUIT arc for them. That's
        a battle even though nobody's got by, and it's what lets an undercut or a late
        crash be recognised as settling a fight the cars couldn't win on track. Inferred
        purely from gaps the director already sees. Also the lap hook a future safety
        car will read to pace a restart."""
        running = [s for s in report.standings if not s.retired]
        close_now = set()
        for i in range(1, len(running)):
            s = running[i]
            if 0 < s.interval <= PURSUIT_GAP:
                ahead = running[i - 1]
                pair = frozenset((s.name, ahead.name))
                close_now.add(pair)
                self.memory.pursuit[pair] = self.memory.pursuit.get(pair, 0) + 1
                if self.memory.pursuit[pair] >= PURSUIT_MIN_LAPS:
                    arc = self.memory.arc_for(pair)
                    if arc is None or arc.resolved:
                        arc = self.memory.open_arc(pair, s.position, report.lap, ahead.name)
                    arc.pursuit = True
                    arc.last_lap = report.lap
        for pair in list(self.memory.pursuit):
            if pair not in close_now:
                self.memory.pursuit[pair] = 0

    def _live_arc(self, pair, lap):
        """The arc for this pair IF it's a current fight worth naming as resolved -- it
        exists, hasn't ended, was active recently, and is a real battle (it has traded
        a place or been a sustained pursuit). Otherwise None."""
        arc = self.memory.arc_for(pair)
        if arc is None or arc.resolved:
            return None
        if lap - arc.last_lap > ARC_LIVE_WINDOW:
            return None
        if arc.exchanges < 1 and not arc.pursuit:
            return None
        return arc
