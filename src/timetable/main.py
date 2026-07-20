"""
Point of entry/orchestrator:
    - load excel entry
    - start solver
    - export results
    - catch errors
"""
import argparse
import sys
from pathlib import Path

from timetable.constants import SLOT_WEIGHTS, TIME_SLOTS
from timetable.excel_export import export_schedule_to_excel, load_teachers_from_excel
from timetable.solver import TimetableSolver

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "data" / "example_entry.xlsx"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "timetable_output.xlsx"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a school timetable from an Excel input file.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to the input Excel file with teacher data.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to write the generated timetable Excel file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        teachers = load_teachers_from_excel(args.input)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}")
        return 1
    except Exception as e:
        print(f"Failed to read input file '{args.input}': {e}")
        return 1

    solver = TimetableSolver(teachers, TIME_SLOTS, slot_weights=SLOT_WEIGHTS)
    solver.build_model()
    result = solver.solve()

    if result is None:
        print("Solver failed to find any solution (unexpected).")
        return 1

    if solver.unresolved_slots:
        print(
            f"Warning: {len(solver.unresolved_slots)} slot(s) could not be staffed: "
            f"{', '.join(solver.unresolved_slots)}"
        )
    else:
        print("All time slots successfully staffed.")

    export_schedule_to_excel(result, TIME_SLOTS, args.output, unresolved_slots=solver.unresolved_slots)
    print(f"Timetable written to: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
