"""Presentation -- turns results into text on screen.

Notice this file imports NOTHING from the rest of the project. It just receives
data and prints it. That independence is the payoff: you could replace this
entire file with a colourful version, or a web page, and never touch the engine.
"""


def format_time(seconds):
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


def print_race_result(cars):
    print("\n  RACE RESULT")
    print("  " + "-" * 52)
    winner_time = cars[0].total_time
    for finish_pos, car in enumerate(cars, start=1):
        gap = car.total_time - winner_time
        gap_str = "WINNER" if finish_pos == 1 else f"+{gap:.3f}"
        moved = car.grid_position - finish_pos
        move_str = f"UP {moved}" if moved > 0 else f"DOWN {-moved}" if moved < 0 else "--"
        print(f"  P{finish_pos:<2} {car.driver.name:<13} {car.driver.team:<9} "
              f"{format_time(car.total_time):<10} {gap_str:<9} (from P{car.grid_position}, {move_str})")
    print()
