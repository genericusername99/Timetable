"""
Entry and exit point of all excel communication. Read in excel entry and export to excel.
"""

import pandas as pd

from timetable.model import Teacher
from timetable.enums.teacher_role import TeacherRole

#
def load_teachers_from_excel(path: str) -> list[Teacher]:
    xls = pd.ExcelFile(path)

    df = pd.read_excel(path, sheet_name=xls.sheet_names[0]) # takes dist sheet on default, can be changed into: sheet_name="teachers" o.s.

    teachers: list[Teacher] = []

    # print("rows found:", df.columns.tolist())

    for _, row in df.iterrows():
        teacher = Teacher(
            id=str(row["id"]),
            name=str(row["name"]),

            subjects={s.strip() for s in row["subjects"].split(",")},
            max_weekly_hours=int(row["max_weekly_hours"]),
            availability={s.strip() for s in row["availability"].split(",")},

            role=TeacherRole(row["role"]),

            is_homeroom_teacher=bool(row["is_homeroom_teacher"]),
            homeroom_class=(
                str(row["homeroom_class"])
                if pd.notna(row["homeroom_class"])
                else None
            ),
        )

        teachers.append(teacher)

    return teachers


def export_schedule_to_excel(
    result: dict[str, list[str]],
    time_slots: list[str],
    output_path: str,
) -> None:
    teacher_ids = sorted(result.keys())

    grid = pd.DataFrame("", index=time_slots, columns=teacher_ids)
    for teacher_id, slots in result.items():
        for slot in slots:
            grid.loc[slot, teacher_id] = "X"

    grid.index.name = "Slot"
    grid.to_excel(output_path, sheet_name="Timetable")


if __name__ == "__main__":
    teachers = load_teachers_from_excel("../data/example_entry.xlsx")

    for t in teachers:
        print(t)
