"""
Entry and exit point of all excel communication. Read in excel entry and export to excel.
"""

import pandas as pd

from timetable.model import SchoolClass, Teacher
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


def load_classes_from_excel(path: str, sheet_name: str = "classes") -> list[SchoolClass]:
    df = pd.read_excel(path, sheet_name=sheet_name)

    classes: list[SchoolClass] = []

    for _, row in df.iterrows():
        required_subjects = {}
        for pair in row["required_subjects"].split(","):
            subject, hours = pair.split(":")
            required_subjects[subject.strip()] = int(hours)

        classes.append(
            SchoolClass(
                id=str(row["class_id"]),
                name=str(row["class_id"]),
                number_of_students=0,
                required_subjects=required_subjects,
            )
        )

    return classes


def export_schedule_to_excel(
    result: dict[str, list[str]],
    time_slots: list[str],
    output_path: str,
    unresolved_slots: list[str] | None = None,
) -> None:
    teacher_ids = sorted(result.keys())

    grid = pd.DataFrame("", index=time_slots, columns=teacher_ids)
    for teacher_id, slots in result.items():
        for slot in slots:
            grid.loc[slot, teacher_id] = "X"

    if unresolved_slots:
        grid["Status"] = ""
        for slot in unresolved_slots:
            grid.loc[slot, "Status"] = "UNSTAFFED"

    grid.index.name = "Slot"
    grid.to_excel(output_path, sheet_name="Timetable")


def export_class_schedule_to_excel(
    schedule: dict[str, dict[str, tuple[str, str]]],
    time_slots: list[str],
    output_path: str,
    subject_shortfall: dict[tuple[str, str], int] | None = None,
) -> None:
    class_ids = sorted(schedule.keys())

    grid = pd.DataFrame("", index=time_slots, columns=class_ids)
    for class_id, lessons in schedule.items():
        for slot, (subject, _teacher_id) in lessons.items():
            grid.loc[slot, class_id] = subject

    grid.index.name = "Slot"
    grid.to_excel(output_path, sheet_name="Timetable")

    if subject_shortfall:
        shortfall_rows = [
            {"class_id": class_id, "subject": subject, "missing_hours": hours}
            for (class_id, subject), hours in subject_shortfall.items()
        ]
        shortfall_df = pd.DataFrame(shortfall_rows)
        with pd.ExcelWriter(output_path, mode="a", engine="openpyxl") as writer:
            shortfall_df.to_excel(writer, sheet_name="Shortfall", index=False)


if __name__ == "__main__":
    teachers = load_teachers_from_excel("../data/example_entry.xlsx")

    for t in teachers:
        print(t)
