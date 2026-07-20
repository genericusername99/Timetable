"""
Test excel_export.py: reading teachers from Excel and writing the solved schedule back out.
"""
from pathlib import Path

import pandas as pd

from timetable.excel_export import (
    export_schedule_to_excel,
    load_classes_from_excel,
    load_teachers_from_excel,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ENTRY_PATH = PROJECT_ROOT / "data" / "example_entry.xlsx"


def test_load_teachers_from_excel_reads_real_file():
    teachers = load_teachers_from_excel(str(EXAMPLE_ENTRY_PATH))

    assert len(teachers) == 9

    homeroom_teachers = {t.homeroom_class: t for t in teachers if t.is_homeroom_teacher}
    assert set(homeroom_teachers) == {"1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b"}

    class_1a_teacher = homeroom_teachers["1a"]
    assert class_1a_teacher.id == "S-R"
    assert class_1a_teacher.subjects == {
        "D", "M/LB", "SU", "M", "Sp", "E", "TW", "BK", "Mus", "D/L",
    }
    assert class_1a_teacher.max_weekly_hours == 30
    assert len(class_1a_teacher.availability) == 35

    specialist = next(t for t in teachers if t.id == "Späth")
    assert specialist.subjects == {"Rel"}
    assert specialist.max_weekly_hours == 31
    assert specialist.is_homeroom_teacher is False
    assert specialist.homeroom_class is None


def test_load_classes_from_excel_reads_real_file():
    classes = load_classes_from_excel(str(EXAMPLE_ENTRY_PATH))

    assert len(classes) == 8
    class_ids = {c.id for c in classes}
    assert class_ids == {"1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b"}

    class_1a = next(c for c in classes if c.id == "1a")
    assert class_1a.required_subjects == {
        "D": 6, "M/LB": 2, "SU": 3, "M": 4, "BK": 1, "Mus": 1, "Sp": 2, "D/L": 1,
    }

    class_2a = next(c for c in classes if c.id == "2a")
    assert class_2a.required_subjects["Rel"] == 2
    assert class_2a.required_subjects["TW"] == 1


def test_export_schedule_to_excel_creates_grid(tmp_path):
    result = {
        "frabai": ["Mo1", "Mo3"],
        "balu": ["Mo2"],
    }
    time_slots = ["Mo1", "Mo2", "Mo3", "Mo4"]
    output_path = tmp_path / "schedule.xlsx"

    export_schedule_to_excel(result, time_slots, str(output_path))

    df = pd.read_excel(output_path, sheet_name="Timetable", index_col=0)

    assert list(df.index) == time_slots
    assert set(df.columns) == {"frabai", "balu"}

    assert df.loc["Mo1", "frabai"] == "X"
    assert df.loc["Mo3", "frabai"] == "X"
    assert df.loc["Mo2", "balu"] == "X"
    assert pd.isna(df.loc["Mo4", "frabai"]) or df.loc["Mo4", "frabai"] == ""
    assert pd.isna(df.loc["Mo1", "balu"]) or df.loc["Mo1", "balu"] == ""


def test_export_schedule_to_excel_marks_unresolved_slots(tmp_path):
    result = {"frabai": ["Mo1"]}
    time_slots = ["Mo1", "Mo2", "Mo3"]
    output_path = tmp_path / "schedule.xlsx"

    export_schedule_to_excel(
        result, time_slots, str(output_path), unresolved_slots=["Mo2", "Mo3"]
    )

    df = pd.read_excel(output_path, sheet_name="Timetable", index_col=0)

    assert "Status" in df.columns
    assert df.loc["Mo2", "Status"] == "UNSTAFFED"
    assert df.loc["Mo3", "Status"] == "UNSTAFFED"
    assert pd.isna(df.loc["Mo1", "Status"]) or df.loc["Mo1", "Status"] == ""
