"""
Test corner cases and simple problems automatically. 
"""
from timetable.model import Teacher
from timetable.enums.teacher_role import TeacherRole
from timetable.solver import TimetableSolver
from timetable.constants import TIME_SLOTS, SLOT_WEIGHTS


def test_single_teacher_single_lesson():
    # arrange
    teacher = Teacher(
        id="frabai",
        name="Franziska Baißbiel",
        subjects={"Mathe"},
        max_weekly_hours=len(TIME_SLOTS),
        availability=set(TIME_SLOTS),
        role=TeacherRole.FULL,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )

    time_slots = TIME_SLOTS

    solver = TimetableSolver(
        teachers=[teacher],
        time_slots=time_slots
    )
    solver.build_model()

    # act
    result = solver.solve()

    # Check solution first
    result = solver.solve()
    assert result is not None, "Solver konnte keinen gültigen Stundenplan finden"


    # Print Lösung für Sichtprüfung
    print("\nSolver Ergebnis:")
    for teacher_id, slots in result.items():
        print(f"{teacher_id}: {slots}")

    # assert
    assert result is not None
    assert "frabai" in result


def test_multiple_teachers_all_slots_covered():
    teacher1 = Teacher(
        id="frabai",
        name="Franziska Baißbiel",
        subjects={"Mathe"},
        max_weekly_hours=len(TIME_SLOTS),
        availability = set(TIME_SLOTS) - {"Mo1", "Mo2", "Mo3", "Mo4"},
        role=TeacherRole.FULL,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )

    teacher2 = Teacher(
        id="balu",
        name="Basel Lula",
        subjects={"Geschichte", "Sport"},
        max_weekly_hours=2,
        availability={"Mo2", "Mo4"},
        role=TeacherRole.PART_TIME,
        is_homeroom_teacher=False,
        homeroom_class=None,
    )

    teacher3 = Teacher(
        id="rosa",
        name="Robin Salzmann",
        subjects={"Geschichte", "MNK"},
        max_weekly_hours=2,
        availability={"Mo1", "Mo3"},
        role=TeacherRole.PART_TIME,
        is_homeroom_teacher=False,
        homeroom_class=None,
    )

    teachers = [teacher1, teacher2, teacher3]
    time_slots = TIME_SLOTS

    solver = TimetableSolver(teachers, time_slots)
    solver.build_model()
    result = solver.solve()

    # Check solution first
    result = solver.solve()
    assert result is not None, "Solver konnte keinen gültigen Stundenplan finden"

    print("\nSolver Ergebnis:")
    for teacher_id, slots in result.items():
        print(f"{teacher_id}: {slots}")

    # Alle Slots abgedeckt?
    covered_slots = set()
    for slots in result.values():
        covered_slots.update(slots)

    assert set(time_slots) == covered_slots

    # Assert: jeder Lehrer bekommt Slots in seiner Availability
    assert result is not None
    for teacher in teachers:
        assert teacher.id in result
        for slot in result[teacher.id]:
            assert slot in teacher.availability


def test_solver_returns_best_fit_when_demand_exceeds_supply():
    # Only one teacher, available for a single slot out of the whole week.
    teacher = Teacher(
        id="frabai",
        name="Franziska Baißbiel",
        subjects={"Mathe"},
        max_weekly_hours=1,
        availability={"Mo1"},
        role=TeacherRole.FULL,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )

    solver = TimetableSolver(teachers=[teacher], time_slots=TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    # Best-fit: still returns a schedule instead of giving up with None.
    assert result is not None
    assert result["frabai"] == ["Mo1"]

    # Everything else is reported as unresolved rather than making the model infeasible.
    assert set(solver.unresolved_slots) == set(TIME_SLOTS) - {"Mo1"}


def test_solver_prioritises_core_hours_over_afternoon_slots():
    # Available for one core slot and one afternoon slot, but can only take one.
    teacher = Teacher(
        id="frabai",
        name="Franziska Baißbiel",
        subjects={"Mathe"},
        max_weekly_hours=1,
        availability={"Mo1", "MoNU"},
        role=TeacherRole.FULL,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )

    time_slots = ["Mo1", "MoNU"]
    solver = TimetableSolver(
        teachers=[teacher],
        time_slots=time_slots,
        slot_weights=SLOT_WEIGHTS,
    )
    solver.build_model()
    result = solver.solve()

    # Core hour ("Mo1") should be filled, afternoon ("MoNU") left uncovered.
    assert result["frabai"] == ["Mo1"]
    assert solver.unresolved_slots == ["MoNU"]