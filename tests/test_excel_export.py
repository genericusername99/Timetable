"""
Test excel_export.py: reading teachers from Excel and writing the solved schedule back out.
"""
from pathlib import Path

import pandas as pd

from timetable.excel_export import export_schedule_to_excel, load_teachers_from_excel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ENTRY_PATH = PROJECT_ROOT / "data" / "example_entry.xlsx"


def test_load_teachers_from_excel_reads_real_file():
    teachers = load_teachers_from_excel(str(EXAMPLE_ENTRY_PATH))

    assert len(teachers) == 3

    frabai = next(t for t in teachers if t.id == "frabai")
    assert frabai.name == "Franziska Baißbiel"
    assert frabai.subjects == {"Deutsch", "Mathe", "Sport"}
    assert frabai.max_weekly_hours == 25
    assert frabai.availability == {"Mo1", "Mo2", "Mo3", "Mo4", "Mo5", "Mo6", "Di1"}
    assert frabai.is_homeroom_teacher is True
    assert frabai.homeroom_class == "1a"

    balu = next(t for t in teachers if t.id == "balu")
    assert balu.max_weekly_hours == 12
    assert balu.availability == {"Mo1", "Mo2", "Mo3", "Mo4", "Mo5"}
    assert balu.is_homeroom_teacher is False
    assert balu.homeroom_class is None


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
