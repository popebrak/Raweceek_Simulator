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

from random import choice

from simulation import QUALIFYING_CUTOFF


# Each cause carries SEVERAL phrasings -- the commentary picks one at random, so the
# same kind of mistake doesn't read the same way twice. {at the corner} is appended
# by the caller. Causes line up with simulation._solo_cause.
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


def render_standings(standings, lap, total_laps):
    lines = [f"  LAP {lap}/{total_laps}", "  " + "-" * 66]
    for s in standings:
        if s.retired:
            lines.append(f"  --  {s.name:<21} {s.team:<15} OUT  (DNF, lap {s.retired_on_lap})")
            continue
        gap_str = "LEADER" if s.position == 1 else f"+{s.gap_to_leader:.3f}"
        lines.append(f"  P{s.position:<2} {s.name:<21} {s.team:<15} "
                     f"{gap_str:<10} last {format_time(s.last_lap)}{_tyre_tag(s)}{_damage_tag(s)}")
    return "\n".join(lines)


# --- COMMENTARY: the spoken voice. Pure prose, never numbers. ----------------
def _at(loc):
    """' at the Parabolica' if we know the corner, '' if we don't."""
    return f" at {loc}" if loc else ""


def render_commentary(inc):
    """One speakable line of commentary for an incident. No telemetry, ever."""
    at = _at(inc.location)
    if inc.cause == "over the limit":
        return f"  >> {inc.driver_name} is hopelessly out of their depth -- throws it away{at}, and OUT!"
    if inc.cause == "damage failure":
        return f"  >> {inc.driver_name}'s earlier damage finally lets go -- OUT OF THE RACE!"
    if inc.cause == "collision":
        other = inc.other_name
        if inc.retirement and inc.other_retired:
            return (f"  >> CONTACT{at}! {inc.driver_name} and {other} collide -- "
                    f"a {inc.severity} one, and they are BOTH OUT OF THE RACE!")
        if inc.other_retired:
            return (f"  >> {inc.driver_name} dives down the inside of {other}{at} -- "
                    f"{other} is tipped into a spin and OUT, {inc.driver_name} limps on!")
        if inc.retirement:
            return (f"  >> {inc.driver_name} throws it up the inside of {other}{at} and comes "
                    f"off worst -- {inc.driver_name} is OUT!")
        word = CONTACT_WORD[inc.severity]
        return (f"  >> {inc.driver_name} dives down the inside of {other}{at} -- "
                f"side by side... and they make {word} contact, both keep going!")
    # solo: the lone errors -- a random phrasing each time, so they never read stale.
    options = CAUSE_PHRASE.get(inc.cause)
    phrase = choice(options) if options else inc.cause
    if inc.retirement:
        return f"  >> {inc.driver_name} {phrase}{at} -- a {inc.severity} one -- AND THAT'S THE END OF THEIR RACE!"
    return f"  >> {inc.driver_name} {phrase}{at} -- {choice(SOLO_FLOURISH[inc.severity])}"


# --- COMMENTARY: completed overtakes (the other half of the racing story). ----
def render_overtake(ov):
    """One speakable line for a clean pass. Drama scales with what's at stake."""
    if ov.location == "the start":
        if ov.position == 1:
            return f"  >> {ov.passer} BEATS them all off the line -- leads into Turn 1!"
        if ov.places_gained >= 4:
            return f"  >> {ov.passer} -- what a launch! Storms up to P{ov.position}!"
        if ov.places_gained >= 2:
            return f"  >> {ov.passer} gets a flier off the line, up to P{ov.position}!"
        return f"  >> {ov.passer} edges ahead at the start, into P{ov.position}."
    at = _at(ov.location)
    if ov.position == 1:
        return f"  >> {ov.passer} sweeps past {ov.passed}{at} -- and takes the LEAD!"
    if ov.position <= 3:
        return f"  >> {ov.passer} forces it past {ov.passed}{at} for P{ov.position}!"
    return f"  >> {ov.passer} gets the move done on {ov.passed}{at}, up into P{ov.position}."


# --- COMMENTARY: pit stops (fresh rubber, at the cost of track position). -----
def render_pit(ps):
    """One speakable line for a pit stop. The number of the stop colours the call."""
    nth = {1: "", 2: "second ", 3: "third "}.get(ps.stop_number, f"{ps.stop_number}th ")
    onto = f" onto {ps.compound}s" if ps.compound else ""
    article = "an" if (ps.old_stint in (11, 18) or str(ps.old_stint).startswith("8")) else "a"
    if ps.stop_number >= 2:
        return (f"  >> {ps.driver_name} is back in for the {nth}time -- "
                f"{article} {ps.old_stint}-lap stint done, switching{onto}.")
    return (f"  >> {ps.driver_name} peels into the pits after {ps.old_stint} laps, "
            f"comes out{onto}.")


# --- COMMENTARY: the undercut (a pass won in the pit lane). --------------------
def render_undercut(uc):
    """One speakable line for an undercut. The fresh tyres, not a move on track,
    did the work -- so the call leans on the strategy, not the corner."""
    earlier = "a lap earlier" if uc.laps_earlier == 1 else f"{uc.laps_earlier} laps earlier"
    if uc.position == 1:
        return (f"  >> THE UNDERCUT IS ON FOR THE LEAD! {uc.undercutter} stopped {earlier} "
                f"than {uc.victim} -- and has taken the lead in the pit lane!")
    return (f"  >> THE UNDERCUT WORKS! {uc.undercutter} boxed {earlier} than {uc.victim}, "
            f"and the fresh rubber vaults them ahead into P{uc.position}.")


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
