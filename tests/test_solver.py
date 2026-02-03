"""
Test corner cases and simple problems automatically. 
E.g. [1 class, 1 teacher, 1 sublect -> desired solution], [1 class, 0 teacher, 1 subject -> no possible solution]
"""
from timetable.model import Teacher
from timetable.enums.teacher_role import TeacherRole
from timetable.solver import TimetableSolver


def test_single_teacher_single_lesson():
    # arrange
    teacher = Teacher(
        id="frabai",
        name="Franziska Baißbiel",
        subjects={"Mathe"},
        max_weekly_hours=5,
        availability={1, 3},
        role=TeacherRole.FULL,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )

    time_slots = [1, 2, 3]

    solver = TimetableSolver(
        teachers=[teacher],
        time_slots=time_slots
    )
    solver.build_model()

    # act
    result = solver.solve()

    # Print Lösung für Sichtprüfung
    print("\nSolver Ergebnis:")
    for teacher_id, slots in result.items():
        print(f"{teacher_id}: {slots}")

    # assert
    assert result is not None
    assert "frabai" in result
    assert len(result["frabai"]) == 1
    assert result["frabai"][0] in {1, 3}



def test_multiple_teachers():
    # Arrange: zwei Lehrer
    teacher1 = Teacher(
        id="frabai",
        name="Franziska Baißbiel",
        subjects={"Mathe"},
        max_weekly_hours=2,
        availability={1, 2, 3},
        role=TeacherRole.FULL,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )

    teacher2 = Teacher(
        id="balu",
        name="Basel Lula",
        subjects={"Geschichte", "Sport"},
        max_weekly_hours=2,
        availability={2, 3, 4},
        role=TeacherRole.PART_TIME,
        is_homeroom_teacher=False,
        homeroom_class=None,
    )

    teachers = [teacher1, teacher2]
    time_slots = [1, 2, 3, 4]

    solver = TimetableSolver(teachers, time_slots)
    solver.build_model()

    # Act
    result = solver.solve()

    # Print Lösung für Sichtprüfung
    print("\nSolver Ergebnis:")
    for teacher_id, slots in result.items():
        print(f"{teacher_id}: {slots}")

    # Assert: jeder Lehrer bekommt Slots in seiner Availability
    assert result is not None
    for teacher in teachers:
        assert teacher.id in result
        for slot in result[teacher.id]:
            assert slot in teacher.availability