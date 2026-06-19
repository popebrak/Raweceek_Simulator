"""Presentation -- builds strings from standings and incidents.

Two distinct jobs live here, and they are kept apart on purpose:

  * COMMENTARY  (render_commentary) -- the spoken voice of the race. Pure prose,
    no numbers, no jargon. This is what a text-to-speech engine will read aloud,
    so it must never contain "+0.22/lap". Severity is expressed in words.

  * TELEMETRY   (render_telemetry, _damage_tag) -- the fiddly engineering bits:
    seconds lost, aero/suspension damage. Useful, but for the timing screen and
    debugging, NOT for the commentary feed. Kept separate so the two never blur.

  * WRAP-UP     (render_summary) -- the post-race story, built from a RaceSummary.
"""

from simulation import QUALIFYING_CUTOFF


# The spoken CALLS -- a pass, a crash, a stop, an undercut -- and their phrasing
# pools (CAUSE_PHRASE / SOLO_FLOURISH / CONTACT_WORD) now live with the booth:
# the words are data in lore.py, the selection is in colour.py (Booth.call_*).
# display.py keeps only the SCREEN furniture and the numeric TELEMETRY below.

# How a retirement reads in the wrap-up, by raw cause (analysis stays wordless).
RETIRE_PHRASE = {
    "collision":      "out in a collision",
    "wall":           "into the wall",
    "kerb":           "broken over a kerb",
    "off-track":      "off and beached",
    "lock-up":        "locked up and off",
    "spin":           "spun out of it",
    "grass":          "off across the grass and out",
    "gravel":         "beached in the gravel",
    "damage failure": "expired from earlier damage",
    "over the limit": "spun out of their depth",
}


def format_time(seconds):
    minutes = int(seconds // 60)
    return f"{minutes}:{seconds % 60:06.3f}"


def print_timing_sheet(results):
    """results: list of (driver, lap, qualified) sorted fastest first."""
    print("\n  QUALIFYING RESULTS")
    print("  " + "-" * 62)
    pole_time = results[0][1]
    cutoff = pole_time * QUALIFYING_CUTOFF
    position = 0
    for driver, lap, qualified in results:
        if qualified:
            position += 1
            gap = lap - pole_time
            gap_str = "POLE" if position == 1 else f"+{gap:.3f}"
            print(f"  P{position:<2} {driver.name:<21} {driver.team:<15} "
                  f"{format_time(lap)}  {gap_str}")
        else:
            print(f"  --  {driver.name:<21} {driver.team:<15} "
                  f"{format_time(lap)}  DNQ (outside 107%)")
    print(f"\n  107% cutoff: {format_time(cutoff)}   (pole {format_time(pole_time)})")
    print()


def _damage_tag(s):
    bits = []
    if s.aero_damage > 0.005:
        bits.append(f"aero +{s.aero_damage:.2f}")
    if s.suspension_damage > 0.005:
        bits.append(f"susp +{s.suspension_damage:.2f}")
    return f"  [{', '.join(bits)}]" if bits else ""


def _tyre_tag(s):
    """Which tyre, and how old -- the higher the age climbs, the slower the lap."""
    if s.stint_laps <= 0:
        return ""
    comp = f"{s.compound[0].upper()} " if s.compound else ""
    return f"  ({comp}{s.stint_laps}L)"


def _penalty_tag(s):
    """A held time penalty the stewards have handed down but the car hasn't served
    yet -- a debt it carries until its next stop, or the flag."""
    pend = getattr(s, "pending_time", 0.0)
    return f"  +{int(round(pend))}s PEN" if pend > 0 else ""


def _weather_tag(conditions):
    """A compact conditions read for the board header: label + air/track temps."""
    if conditions is None:
        return ""
    return (f"   |   {conditions.label.upper()}"
            f"   air {round(conditions.air_temp)}C  track {round(conditions.track_temp)}C")


def render_standings(standings, lap, total_laps, conditions=None):
    lines = [f"  LAP {lap}/{total_laps}{_weather_tag(conditions)}", "  " + "-" * 66]
    for s in standings:
        if s.retired:
            lines.append(f"  --  {s.name:<21} {s.team:<15} OUT  (DNF, lap {s.retired_on_lap})")
            continue
        gap_str = "LEADER" if s.position == 1 else f"+{s.gap_to_leader:.3f}"
        lines.append(f"  P{s.position:<2} {s.name:<21} {s.team:<15} "
                     f"{gap_str:<10} last {format_time(s.last_lap)}{_tyre_tag(s)}{_penalty_tag(s)}{_damage_tag(s)}")
    return "\n".join(lines)


# --- TELEMETRY: the fiddly bits. Numbers live HERE, not in commentary. -------
def render_telemetry(inc):
    """The engineering detail for one incident: time lost, damage picked up.

    Returns "" when there is nothing numeric worth showing (e.g. a retirement,
    where the car's race is simply over). This is for the timing screen / a debug
    stream -- deliberately NOT mixed into the spoken commentary.
    """
    if inc.retirement or inc.other_retired:
        return ""
    bits = []
    if inc.time_lost > 0.05:
        bits.append(f"lost {inc.time_lost:.1f}s")
    if inc.aero_added > 0.01:
        bits.append(f"aero +{inc.aero_added:.2f}/lap")
    if inc.suspension_added > 0.01:
        bits.append(f"susp +{inc.suspension_added:.2f}/lap")
    return f"  ~ {inc.driver_name}: {', '.join(bits)}" if bits else ""


def render_result(standings):
    lines = ["  FINAL CLASSIFICATION", "  " + "-" * 66]
    finishers = [s for s in standings if not s.retired]
    winner_time = finishers[0].total_time if finishers else 0.0
    for s in standings:
        if s.retired:
            lines.append(f"  --  {s.name:<21} {s.team:<15} DNF (lap {s.retired_on_lap}, "
                         f"from P{s.grid_position})")
            continue
        gap = s.total_time - winner_time
        gap_str = "WINNER" if s.position == 1 else f"+{gap:.3f}"
        moved = s.grid_position - s.position
        move_str = f"UP {moved}" if moved > 0 else f"DOWN {-moved}" if moved < 0 else "--"
        tag = "  [damaged]" if s.damage > 0.005 else ""
        lines.append(f"  P{s.position:<2} {s.name:<21} {s.team:<15} "
                     f"{format_time(s.total_time):<10} {gap_str:<9} (from P{s.grid_position}, {move_str}){tag}")
    return "\n".join(lines)


# --- WRAP-UP: the post-race story, built from a RaceSummary. -----------------
def render_summary(summary):
    """Turn a RaceSummary into a spoken-style post-race wrap-up (TTS-ready)."""
    s = summary
    lines = ["  POST-RACE WRAP-UP", "  " + "-" * 66]

    # The headline.
    where = f" at {s.circuit}" if s.circuit else ""
    if s.winner_from == 1:
        win = (f"{s.winner} converts pole into victory for {s.team}{where}, "
               f"leading from lights to flag.")
    else:
        win = (f"{s.winner} wins for {s.team}{where}, climbing from P{s.winner_from} on the grid.")
    lines.append("  " + win)

    # The fight at the front.
    if s.lead_changes == 0:
        lines.append(f"  The lead never changed hands all {s.total_laps} laps.")
    elif s.lead_changes == 1:
        lines.append(f"  The lead changed hands once across the {s.total_laps} laps.")
    else:
        lines.append(f"  A proper scrap up front -- the lead changed hands "
                     f"{s.lead_changes} times.")

    # The podium.
    if len(s.podium) >= 3:
        p2, p3 = s.podium[1], s.podium[2]
        lines.append(f"  {p2[1]} ({p2[2]}) and {p3[1]} ({p3[2]}) completed the podium.")

    # Drive of the day.
    if s.drive_of_the_day:
        name, gained = s.drive_of_the_day
        lines.append(f"  Drive of the day goes to {name}, up {gained} "
                     f"place{'s' if gained != 1 else ''} from where they started.")

    # The casualty list.
    if not s.retirements:
        lines.append(f"  A clean race -- all {s.finishers} starters saw the flag.")
    else:
        lines.append(f"  {s.finishers} of {s.starters} cars made the finish.")
        for name, lap, cause, loc in s.retirements:
            phrase = RETIRE_PHRASE.get(cause, cause)
            where = f" at {loc}" if loc and cause != "damage failure" else ""
            lines.append(f"     - {name}: {phrase}{where} (lap {lap})")
        for a, b, lap, loc in s.double_dnfs:
            where = f" at {loc}" if loc else ""
            lines.append(f"  The biggest flashpoint: {a} and {b} taking each "
                         f"other out{where} on lap {lap}.")

    # Fastest lap (approximate -- see note in simulation.summarize_race).
    if s.fastest_lap_driver:
        lines.append(f"  Fastest lap of the race: {s.fastest_lap_driver}, "
                     f"a {format_time(s.fastest_lap_time)}.")

    # How much racing there was at the sharp end.
    if s.overtakes_count:
        lines.append(f"  {s.overtakes_count} passes for the podium places out on track.")

    # And how much of it was won in the pits.
    if s.undercuts_count:
        moves = "undercut paid off" if s.undercuts_count == 1 else "undercuts paid off"
        lines.append(f"  {s.undercuts_count} {moves} in the pit lane.")

    # The stewards' afternoon: verdicts handed down, and any flag-time reshuffle.
    penalties = getattr(s, "penalties", [])
    if penalties:
        n = len(penalties)
        lines.append(f"  The stewards were busy: {n} penalt{'y' if n == 1 else 'ies'} handed down.")
        for name, offence, kind, lap in penalties:
            verdict = {"time": "time penalty", "drive-through": "drive-through",
                       "stop-go": "stop-go", "dsq": "DISQUALIFIED",
                       "warning": "warning"}.get(kind, kind)
            lines.append(f"     - {name}: {verdict} for {offence} (lap {lap})")
    for name, prov, off in getattr(s, "reclassified", []):
        lines.append(f"  Stewards' reclassification: {name} crossed the line P{prov}, classified P{off}.")

    return "\n".join(lines)


def track_banner(track):
    """The pre-race title card: which Grand Prix, where, how long, what to expect."""
    return "\n".join([
        "  " + "=" * 62,
        f"  {track.name.upper()}",
        f"  {track.circuit}, {track.country}   --   {track.laps} laps",
        f"  {track.character}",
        "  " + "=" * 62,
    ])
