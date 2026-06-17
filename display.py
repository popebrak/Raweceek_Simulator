"""Presentation -- builds strings from standings and incidents."""

from simulation import QUALIFYING_CUTOFF


CAUSE_PHRASE = {
    "off-track": "runs wide",
    "kerb": "is launched over a sausage kerb",
    "wall": "clips the wall",
    "contact": "makes contact",
}


def format_time(seconds):
    minutes = int(seconds // 60)
    return f"{minutes}:{seconds % 60:06.3f}"


def print_timing_sheet(results):
    """results: list of (driver, lap, qualified) sorted fastest first."""
    print("\n  QUALIFYING RESULTS")
    print("  " + "-" * 56)
    pole_time = results[0][1]
    cutoff = pole_time * QUALIFYING_CUTOFF
    position = 0
    for driver, lap, qualified in results:
        if qualified:
            position += 1
            gap = lap - pole_time
            gap_str = "POLE" if position == 1 else f"+{gap:.3f}"
            print(f"  P{position:<2} {driver.name:<19} {driver.team:<13} "
                  f"{format_time(lap)}  {gap_str}")
        else:
            print(f"  --  {driver.name:<19} {driver.team:<13} "
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


def render_standings(standings, lap, total_laps):
    lines = [f"  LAP {lap}/{total_laps}", "  " + "-" * 60]
    for s in standings:
        if s.retired:
            lines.append(f"  --  {s.name:<19} {s.team:<13} OUT  (DNF, lap {s.retired_on_lap})")
            continue
        gap_str = "LEADER" if s.position == 1 else f"+{s.gap_to_leader:.3f}"
        lines.append(f"  P{s.position:<2} {s.name:<19} {s.team:<13} "
                     f"{gap_str:<10} last {s.last_lap:6.3f}{_damage_tag(s)}")
    return "\n".join(lines)


def render_incident(inc):
    if inc.cause == "damage failure":
        return f"  >> {inc.driver_name}'s earlier damage finally lets go -- OUT OF THE RACE!"
    phrase = CAUSE_PHRASE.get(inc.cause, inc.cause)
    if inc.retirement:
        return f"  >> {inc.driver_name} {phrase} -- a {inc.severity} one -- AND THAT'S THE END OF THEIR RACE!"
    effects = []
    if inc.time_lost > 0.05:
        effects.append(f"loses {inc.time_lost:.1f}s")
    if inc.aero_added > 0.01:
        effects.append(f"aero +{inc.aero_added:.2f}/lap")
    if inc.suspension_added > 0.01:
        effects.append(f"suspension +{inc.suspension_added:.2f}/lap")
    detail = "; ".join(effects) if effects else "but gets away with it"
    return f"  >> {inc.driver_name} {phrase} ({inc.severity}) -- {detail}"


def render_result(standings):
    lines = ["  FINAL CLASSIFICATION", "  " + "-" * 60]
    finishers = [s for s in standings if not s.retired]
    winner_time = finishers[0].total_time if finishers else 0.0
    for s in standings:
        if s.retired:
            lines.append(f"  --  {s.name:<19} {s.team:<13} DNF (lap {s.retired_on_lap}, "
                         f"from P{s.grid_position})")
            continue
        gap = s.total_time - winner_time
        gap_str = "WINNER" if s.position == 1 else f"+{gap:.3f}"
        moved = s.grid_position - s.position
        move_str = f"UP {moved}" if moved > 0 else f"DOWN {-moved}" if moved < 0 else "--"
        tag = "  [damaged]" if s.damage > 0.005 else ""
        lines.append(f"  P{s.position:<2} {s.name:<19} {s.team:<13} "
                     f"{format_time(s.total_time):<10} {gap_str:<9} (from P{s.grid_position}, {move_str}){tag}")
    return "\n".join(lines)
