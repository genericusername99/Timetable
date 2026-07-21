# Timetable

A CP-SAT (Google OR-Tools) solver that builds a weekly elementary-school
timetable from an Excel file of teachers and classes, and writes the result
back out as a colored, formatted Excel schedule.

## What it does

Given a list of teachers (subjects they're qualified for, weekly availability,
max hours, homeroom assignment) and a list of classes (required weekly hours
per subject), the solver assigns teacher → class → subject → time-slot so
that:

- Every class gets as close as possible to its required weekly hours per
  subject (soft constraint: shortfall is minimized, not required to be zero,
  so the solver still produces a best-effort schedule instead of failing
  outright when the input can't be fully satisfied).
- A class's own homeroom teacher is preferred over another qualified teacher
  for that class's lessons.
- A teacher is never scheduled in two classes at the same time slot.
- A class is never scheduled with two lessons at the same time slot.
- No teacher exceeds their max weekly hours.
- The gym ("Sp") is only used by one class at a time, regardless of teacher.
- Regular lessons only run periods 1–5; period 6 is always left free.
- Each class gets exactly one afternoon ("NU") slot per week, and parallel
  classes in the same grade (e.g. "1a"/"1b") always share the same NU
  weekday (which weekday it is is left for the solver to decide).
- Within periods 1–5, a free period may only fall at the start or end of the
  day — never sandwiched between two used periods.

## Data flow

```
main.py
  │
  ├─ excel_export.py   → read teachers + classes from an input .xlsx
  ├─ model.py          → Teacher / SchoolClass data structures
  ├─ solver.py         → build & solve the CP-SAT model
  └─ excel_export.py   → write the solved schedule to an output .xlsx
```

- `constants.py` — weekdays, periods, and the derived list of time slots
  (e.g. `"Mo1"`, `"Di3"`, `"FrNU"`).
- `model.py` — `Teacher` and `SchoolClass` dataclasses.
- `solver.py` — `TimetableSolver`: builds the CP-SAT model (`build_model()`)
  and solves it (`solve()`), returning `class_id → slot → (subject,
  teacher_id)` plus a `subject_shortfall` dict for any unmet hours.
- `excel_export.py` — Excel I/O: `load_teachers_from_excel`,
  `load_classes_from_excel`, and `export_colored_class_schedule_to_excel`
  (per-teacher cell coloring, grade grouping, legend, required-hours summary
  — styled after `data/format.xlsx`).
- `main.py` — orchestrates the three steps above and handles CLI args /
  errors.

## Project setup

Two virtual environments exist depending on where you run from:

- **Native Windows (PowerShell)** — `.venv-win`. Use this for everyday
  development on Windows:
  ```
  .venv-win\Scripts\Activate.ps1
  ```
- **WSL** — `.venv`. Use this when working from a WSL shell:
  ```
  source .venv/bin/activate
  ```

A fresh terminal always starts unactivated — reactivate the matching venv
before running anything below.

## Running the tests

```
pytest
```

(`pytest.ini` sets `pythonpath = src`, so no extra environment variable is
needed.)

## Running the app (development)

```
PYTHONPATH=src python -m timetable.main
```

By default this reads `data/example_entry.xlsx` and writes
`data/timetable_output.xlsx`. Override either with:

```
PYTHONPATH=src python -m timetable.main --input path/to/input.xlsx --output path/to/output.xlsx
```

## Building the standalone .exe

For non-technical users, the app can be packaged into a single `.exe` that
needs no Python install:

```
pyinstaller --onefile --name Timetable --paths src --collect-all ortools --clean --noconfirm src/timetable/main.py
```

This produces `dist/Timetable.exe`. When run directly (double-clicked), it
looks for `input.xlsx` next to the exe and writes `output.xlsx` there —
no `--input`/`--output` flags needed. The console window stays open after
it finishes so the result is readable before closing it.

**Rebuilding:** the exe is a manual build artifact — it does not update
itself when the source changes. After making changes you want a
distributed copy to have, rerun the command above and replace the old
`Timetable.exe` with the new one.

**Distributing:** put `Timetable.exe`, an `input.xlsx`, and a short
usage note in one folder (see `dist/for_mother/` for an example) and
share that folder (USB stick or a cloud-synced folder — the exe is too
large for most email attachments). First run may trigger a Windows
SmartScreen warning since the exe is unsigned; click "More info" → "Run
anyway".

## Data files

- `data/example_entry.xlsx` — example/test input (teachers on the first
  sheet, classes on the `"classes"` sheet).
- `data/format.xlsx` — reference file showing the target output layout and
  coloring style.
- `data/timetable_output.xlsx` — default dev-run output (gitignored).
