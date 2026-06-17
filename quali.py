"""
Race Weekend Simulator -- Milestone 1
A single qualifying session, simulated and printed as a timing sheet.
"""

import random
from dataclasses import dataclass


@dataclass
class Driver:
    name: str
    team: str
    pace: float          # base lap time in seconds -- lower is faster
    consistency: float   # lap-to-lap variation in seconds -- lower is steadier


# A small starting grid. Tweak these numbers and see what happens.
GRID = [
    Driver("Alex Mercer",  "Velocity", 89.8, 0.15),
    Driver("Rohan Patel",  "Velocity", 89.9, 0.20),
    Driver("Lena Brandt",  "Apex",     90.0, 0.18),
    Driver("Diego Santos", "Apex",     90.1, 0.22),
    Driver("Yuki Tanaka",  "Meridian", 90.2, 0.17),
    Driver("Sofia Rossi",  "Meridian", 90.3, 0.25),
    Driver("Omar Haddad",  "Crest",    90.4, 0.20),
    Driver("Ingrid Voss",  "Crest",    90.5, 0.28),
    Driver("Caleb North",  "Pinnacle", 90.6, 0.24),
    Driver("Mira Sokolov", "Pinnacle", 90.7, 0.30),
]


def simulate_lap(driver):
    """Return one lap time: base pace plus some random variation."""
    variation = random.gauss(0, driver.consistency)
    return driver.pace + variation


def run_qualifying(grid):
    """Each driver sets one flying lap. Return (driver, lap) sorted fastest first."""
    results = [(driver, simulate_lap(driver)) for driver in grid]
    results.sort(key=lambda pair: pair[1])
    return results


def format_time(seconds):
    """Turn 89.843 into '1:29.843' like a real timing screen."""
    minutes = int(seconds // 60)
    remainder = seconds % 60
    return f"{minutes}:{remainder:06.3f}"


def print_timing_sheet(results):
    print("\n  QUALIFYING RESULTS")
    print("  " + "-" * 40)
    pole_time = results[0][1]
    for position, (driver, lap) in enumerate(results, start=1):
        gap = lap - pole_time
        gap_str = "POLE" if position == 1 else f"+{gap:.3f}"
        print(f"  P{position:<2} {driver.name:<13} {driver.team:<9} "
              f"{format_time(lap)}  {gap_str}")
    print()


if __name__ == "__main__":
    results = run_qualifying(GRID)
    print_timing_sheet(results)

