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

from timetable.constants import TIME_SLOTS
from timetable.excel_export import (
    export_colored_class_schedule_to_excel,
    load_classes_from_excel,
    load_teachers_from_excel,
)
from timetable.solver import TimetableSolver

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _app_dir() -> Path:
    """Folder the input/output files default to.

    When frozen into a standalone .exe (PyInstaller), that's the folder the
    .exe itself lives in, so a double-click user only has to drop an input
    file next to it. In normal (dev) runs it stays the project's data/ dir.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT / "data"


if getattr(sys, "frozen", False):
    DEFAULT_INPUT = _app_dir() / "input.xlsx"
    DEFAULT_OUTPUT = _app_dir() / "output.xlsx"
else:
    DEFAULT_INPUT = _app_dir() / "example_entry.xlsx"
    DEFAULT_OUTPUT = _app_dir() / "timetable_output.xlsx"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a school timetable from an Excel input file.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Path to the input Excel file with teacher and class data.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to write the generated timetable Excel file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        teachers = load_teachers_from_excel(args.input)
        classes = load_classes_from_excel(args.input)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}")
        return 1
    except Exception as e:
        print(f"Failed to read input file '{args.input}': {e}")
        return 1

    try:
        solver = TimetableSolver(teachers, classes, TIME_SLOTS)
        solver.build_model()
        result = solver.solve()

        if result is None:
            print("Solver failed to find any solution (unexpected).")
            return 1

        if solver.subject_shortfall:
            print(f"Warning: {len(solver.subject_shortfall)} subject requirement(s) could not be fully met:")
            for (class_id, subject), missing_hours in solver.subject_shortfall.items():
                print(f"  {class_id}: {subject} short by {missing_hours}h")
        else:
            print("All classes fully staffed for their required subject hours.")

        export_colored_class_schedule_to_excel(
            result, teachers, classes, TIME_SLOTS, args.output, subject_shortfall=solver.subject_shortfall
        )
        print(f"Timetable written to: {args.output}")
        return 0
    except Exception as e:
        print(f"Unexpected error while generating the timetable: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    if getattr(sys, "frozen", False):
        # Keep the console window open so a double-click user can read the
        # result/errors above instead of it flashing shut immediately.
        input("\nPress Enter to close this window...")
    sys.exit(exit_code)
