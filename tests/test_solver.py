"""
Test corner cases and simple problems automatically.
"""
from timetable.model import SchoolClass, Teacher
from timetable.enums.teacher_role import TeacherRole
from timetable.solver import TimetableSolver
from timetable.constants import TIME_SLOTS


def make_teacher(id, subjects, availability=TIME_SLOTS, max_weekly_hours=None, is_homeroom_teacher=False, homeroom_class=None):
    return Teacher(
        id=id,
        name=id,
        subjects=set(subjects),
        max_weekly_hours=max_weekly_hours if max_weekly_hours is not None else len(TIME_SLOTS),
        availability=set(availability),
        role=TeacherRole.FULL,
        is_homeroom_teacher=is_homeroom_teacher,
        homeroom_class=homeroom_class,
    )


def test_class_gets_required_hours_from_own_homeroom_teacher():
    teacher = make_teacher(
        "frabai", subjects={"D", "M"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    school_class = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"D": 3, "M": 2}
    )

    solver = TimetableSolver([teacher], [school_class], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    assert solver.subject_shortfall == {}

    lessons = result["1a"]
    assert sum(1 for subject, teacher_id in lessons.values() if subject == "D") == 3
    assert sum(1 for subject, teacher_id in lessons.values() if subject == "M") == 2
    assert all(teacher_id == "frabai" for _, teacher_id in lessons.values())


def test_shortfall_when_no_qualified_teacher_available():
    teacher = make_teacher(
        "frabai", subjects={"D"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    school_class = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"D": 2, "Rel": 2}
    )

    solver = TimetableSolver([teacher], [school_class], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    assert solver.subject_shortfall == {("1a", "Rel"): 2}
    lessons = result["1a"]
    assert sum(1 for subject, _ in lessons.values() if subject == "D") == 2
    assert all(subject != "Rel" for subject, _ in lessons.values())


def test_specialist_teacher_covers_subject_across_classes():
    # Mirrors the real setup: one teacher qualified ONLY for "Rel", homeroom
    # teachers qualified for everything except "Rel" -- the specialist should
    # end up covering "Rel" for every class that needs it, purely from the
    # qualification constraint (no separate specialist field). Each class also
    # needs "D" from its own homeroom teacher, so its mandatory weekly NU slot
    # (shared with its parallel class, see below) can be filled with "D" rather
    # than forcing the single specialist to teach both classes' "Rel" at the
    # exact same NU slot on their shared NU day.
    specialist = make_teacher("spaeth", subjects={"Rel"})
    homeroom_a = make_teacher(
        "teacher_a", subjects={"D", "M"}, is_homeroom_teacher=True, homeroom_class="2a"
    )
    homeroom_b = make_teacher(
        "teacher_b", subjects={"D", "M"}, is_homeroom_teacher=True, homeroom_class="2b"
    )
    class_a = SchoolClass(
        id="2a", name="2a", number_of_students=20, required_subjects={"Rel": 2, "D": 3}
    )
    class_b = SchoolClass(
        id="2b", name="2b", number_of_students=20, required_subjects={"Rel": 2, "D": 3}
    )

    solver = TimetableSolver([specialist, homeroom_a, homeroom_b], [class_a, class_b], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert solver.subject_shortfall == {}
    for class_id in ("2a", "2b"):
        rel_lessons = {
            slot: teacher_id
            for slot, (subject, teacher_id) in result[class_id].items()
            if subject == "Rel"
        }
        assert len(rel_lessons) == 2
        assert all(teacher_id == "spaeth" for teacher_id in rel_lessons.values())


def test_gym_only_used_by_one_class_at_a_time():
    # Each class also needs "D" from its own homeroom so its mandatory weekly
    # NU slot (shared with its parallel class) can be filled with "D" instead
    # of forcing both classes into the gym-exclusive "Sp" at the same slot.
    teacher_a = make_teacher(
        "teacher_a", subjects={"Sp", "D"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    teacher_b = make_teacher(
        "teacher_b", subjects={"Sp", "D"}, is_homeroom_teacher=True, homeroom_class="1b"
    )
    class_a = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"Sp": 4, "D": 2}
    )
    class_b = SchoolClass(
        id="1b", name="1b", number_of_students=20, required_subjects={"Sp": 4, "D": 2}
    )

    solver = TimetableSolver([teacher_a, teacher_b], [class_a, class_b], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    for slot in TIME_SLOTS:
        classes_in_gym = sum(
            1
            for class_id in ("1a", "1b")
            if slot in result.get(class_id, {}) and result[class_id][slot][0] == "Sp"
        )
        assert classes_in_gym <= 1


def test_teacher_never_double_booked_across_classes():
    # Capacity covers both classes' full demand (6) rather than forcing one to
    # zero hours -- a class with zero assigned hours can't also satisfy the
    # "exactly one NU slot per week" rule, which is a separate concern from
    # what this test checks (that one teacher is never in two places at once).
    # Classes are in different grades ("1a"/"2a") so they aren't forced to
    # share the same NU weekday -- with only "D" available to either class,
    # same-grade parallel classes would otherwise be forced to both need the
    # shared teacher at the exact same NU slot, which is a separate conflict
    # from what this test checks.
    shared_teacher = make_teacher("shared", subjects={"D"}, max_weekly_hours=6)
    class_a = SchoolClass(id="1a", name="1a", number_of_students=20, required_subjects={"D": 3})
    class_b = SchoolClass(id="2a", name="2a", number_of_students=20, required_subjects={"D": 3})

    solver = TimetableSolver([shared_teacher], [class_a, class_b], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    for slot in TIME_SLOTS:
        classes_taught = sum(
            1
            for class_id in ("1a", "2a")
            if slot in result.get(class_id, {}) and result[class_id][slot][1] == "shared"
        )
        assert classes_taught <= 1


def test_homeroom_teacher_preferred_over_other_qualified_teacher():
    homeroom = make_teacher(
        "homeroom", subjects={"D"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    other = make_teacher("other", subjects={"D"})
    school_class = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"D": 3}
    )

    solver = TimetableSolver([homeroom, other], [school_class], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    lessons = result["1a"]
    assert all(teacher_id == "homeroom" for _, teacher_id in lessons.values())


def test_no_lessons_scheduled_in_period_6():
    teacher = make_teacher(
        "frabai", subjects={"D"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    school_class = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"D": 3}
    )

    solver = TimetableSolver([teacher], [school_class], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    lessons = result["1a"]
    assert all(slot[2:] != "6" for slot in lessons)


def test_class_has_exactly_one_afternoon_slot_per_week():
    teacher = make_teacher(
        "frabai", subjects={"D"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    school_class = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"D": 5}
    )

    solver = TimetableSolver([teacher], [school_class], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    lessons = result["1a"]
    afternoon_slots_used = [slot for slot in lessons if slot.endswith("NU")]
    assert len(afternoon_slots_used) == 1


def test_parallel_classes_share_same_afternoon_day():
    teacher_a = make_teacher(
        "teacher_a", subjects={"D"}, is_homeroom_teacher=True, homeroom_class="1a"
    )
    teacher_b = make_teacher(
        "teacher_b", subjects={"D"}, is_homeroom_teacher=True, homeroom_class="1b"
    )
    class_a = SchoolClass(id="1a", name="1a", number_of_students=20, required_subjects={"D": 5})
    class_b = SchoolClass(id="1b", name="1b", number_of_students=20, required_subjects={"D": 5})

    solver = TimetableSolver([teacher_a, teacher_b], [class_a, class_b], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None

    def afternoon_day(class_id):
        return next(slot[:2] for slot in result[class_id] if slot.endswith("NU"))

    assert afternoon_day("1a") == afternoon_day("1b")


def test_no_free_period_sandwiched_between_lessons():
    # Teacher only available Monday periods 1, 3, 5 (plus one NU slot for the
    # mandatory afternoon lesson). Using any 2 of {Mo1, Mo3, Mo5} would leave an
    # unavailable (always-free) period sandwiched between two used ones, which
    # the "no middle gap" rule forbids -- so at most 1 of those 3 morning slots
    # can be used, and the rest of "D": 3 is absorbed as shortfall rather than
    # the model becoming outright infeasible.
    limited_availability = {"Mo1", "Mo3", "Mo5", "MoNU"}
    teacher = make_teacher(
        "frabai",
        subjects={"D"},
        availability=limited_availability,
        is_homeroom_teacher=True,
        homeroom_class="1a",
    )
    school_class = SchoolClass(
        id="1a", name="1a", number_of_students=20, required_subjects={"D": 3}
    )

    solver = TimetableSolver([teacher], [school_class], TIME_SLOTS)
    solver.build_model()
    result = solver.solve()

    assert result is not None
    lessons = result["1a"]
    morning_slots_used = [slot for slot in lessons if slot in {"Mo1", "Mo3", "Mo5"}]
    assert len(morning_slots_used) <= 1
    assert solver.subject_shortfall.get(("1a", "D"), 0) >= 1
