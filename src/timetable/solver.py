"""
Solve problem with OR-tools, Define Constraints, (export solutions?) -> NO EXCEL DEPENDENCIES!!!!
"""
from ortools.sat.python import cp_model
from timetable.model import SchoolClass, Teacher
from timetable.constants import WEEKDAYS, AFTERNOON

# Objective weights, staggered by an order of magnitude so a higher-priority
# goal is never sacrificed to improve a lower-priority one: fulfilling required
# subject hours matters far more than which qualified teacher ends up teaching it.
SHORTFALL_WEIGHT = 10000
NON_HOMEROOM_WEIGHT = 10

# Regular lessons only run periods 1-5; the 6th hour is always left free.
REGULAR_PERIODS = ["1", "2", "3", "4", "5"]


class TimetableSolver:
    def __init__(
        self,
        teachers: list[Teacher],
        classes: list[SchoolClass],
        time_slots: list[str],
        gym_subject: str = "Sp",
    ):
        self.teachers = teachers
        self.classes = classes
        self.time_slots = time_slots
        self.gym_subject = gym_subject
        self.model = cp_model.CpModel()

        self.assign = {}  # (teacher_id, class_id, subject, slot) -> BoolVar
        self.shortfall = {}  # (class_id, subject) -> IntVar
        self.subject_shortfall: dict[tuple[str, str], int] = {}

        self.homeroom_teacher_id = {
            teacher.homeroom_class: teacher.id
            for teacher in self.teachers
            if teacher.is_homeroom_teacher and teacher.homeroom_class is not None
        }

    def build_model(self):
        """
        Create decision variables and constraints:
            - swimming only noon due to swimming gym -> if class a has swimming then class b should have sport in the noon so we can switch them easily
            - find more...
        """

        # Decision variables: assign[(teacher_id, class_id, subject, slot)] = 1 if
        # that teacher teaches that class that subject at that slot. Only created
        # where the teacher is qualified, available, and the class actually needs
        # the subject -- this encodes qualification/availability directly instead
        # of via separate == 0 constraints. Period 6 slots are skipped entirely so
        # regular lessons can never be scheduled there.
        for teacher in self.teachers:
            for school_class in self.classes:
                subjects = teacher.subjects & set(school_class.required_subjects)
                for subject in subjects:
                    for slot in self.time_slots:
                        if slot[2:] == "6":
                            continue
                        if slot in teacher.availability:
                            self.assign[(teacher.id, school_class.id, subject, slot)] = (
                                self.model.NewBoolVar(
                                    f"assign_{teacher.id}_{school_class.id}_{subject}_{slot}"
                                )
                            )

        # Constraint: a teacher can teach at most one (class, subject) per slot,
        # across all classes.
        for teacher in self.teachers:
            for slot in self.time_slots:
                vars_at_slot = [
                    var
                    for (t_id, _, _, s), var in self.assign.items()
                    if t_id == teacher.id and s == slot
                ]
                if vars_at_slot:
                    self.model.Add(sum(vars_at_slot) <= 1)

        # Constraint: a class can have at most one (teacher, subject) per slot.
        for school_class in self.classes:
            for slot in self.time_slots:
                vars_at_slot = [
                    var
                    for (_, c_id, _, s), var in self.assign.items()
                    if c_id == school_class.id and s == slot
                ]
                if vars_at_slot:
                    self.model.Add(sum(vars_at_slot) <= 1)

        # Constraint: required weekly hours per (class, subject), soft via a
        # shortfall slack -- never over-teach (shortfall >= 0 forces assigned
        # <= required), and under-teaching is only allowed against the objective
        # penalty below.
        for school_class in self.classes:
            for subject, required_hours in school_class.required_subjects.items():
                vars_for_subject = [
                    var
                    for (_, c_id, subj, _), var in self.assign.items()
                    if c_id == school_class.id and subj == subject
                ]
                shortfall_var = self.model.NewIntVar(
                    0, required_hours, f"shortfall_{school_class.id}_{subject}"
                )
                self.shortfall[(school_class.id, subject)] = shortfall_var
                self.model.Add(sum(vars_for_subject) + shortfall_var == required_hours)

        # Constraint: max weekly hours per teacher, across all classes/subjects.
        for teacher in self.teachers:
            vars_for_teacher = [
                var for (t_id, _, _, _), var in self.assign.items() if t_id == teacher.id
            ]
            if vars_for_teacher:
                self.model.Add(sum(vars_for_teacher) <= teacher.max_weekly_hours)

        # Constraint: only one class can use the gym at a time, regardless of teacher.
        for slot in self.time_slots:
            vars_in_gym = [
                var
                for (_, _, subj, s), var in self.assign.items()
                if subj == self.gym_subject and s == slot
            ]
            if vars_in_gym:
                self.model.Add(sum(vars_in_gym) <= 1)

        self._add_afternoon_constraints()
        self._add_no_middle_gap_constraints()

        # Objective: minimise shortfall first (dominant weight), then prefer the
        # class's own homeroom teacher over any other qualified teacher.
        non_homeroom_vars = [
            var
            for (t_id, c_id, _, _), var in self.assign.items()
            if self.homeroom_teacher_id.get(c_id) != t_id
        ]
        self.model.Minimize(
            SHORTFALL_WEIGHT * sum(self.shortfall.values())
            + NON_HOMEROOM_WEIGHT * sum(non_homeroom_vars)
        )

    def _used_var(self, class_id: str, slot: str) -> cp_model.IntVar:
        """A BoolVar equal to whether `class_id` has any lesson at `slot`."""
        vars_at_slot = [
            var
            for (_, c_id, _, s), var in self.assign.items()
            if c_id == class_id and s == slot
        ]
        used_var = self.model.NewBoolVar(f"used_{class_id}_{slot}")
        if vars_at_slot:
            self.model.Add(used_var == sum(vars_at_slot))
        else:
            self.model.Add(used_var == 0)
        return used_var

    def _add_afternoon_constraints(self):
        """
        Each class gets exactly one "NU" (afternoon) slot per week, and parallel
        classes (same grade, e.g. "1a"/"1b") must share the same NU weekday --
        which weekday that is stays free for the solver to pick.
        """
        nu_used = {
            (school_class.id, day): self._used_var(school_class.id, f"{day}{AFTERNOON}")
            for school_class in self.classes
            for day in WEEKDAYS
        }

        for school_class in self.classes:
            self.model.Add(
                sum(nu_used[(school_class.id, day)] for day in WEEKDAYS) == 1
            )

        classes_by_grade: dict[str, list[str]] = {}
        for school_class in self.classes:
            classes_by_grade.setdefault(school_class.id[:-1], []).append(school_class.id)

        for grade_class_ids in classes_by_grade.values():
            anchor, *others = grade_class_ids
            for other in others:
                for day in WEEKDAYS:
                    self.model.Add(nu_used[(anchor, day)] == nu_used[(other, day)])

    def _add_no_middle_gap_constraints(self):
        """
        Within periods 1-5, a free period may only sit at the start or end of the
        day -- never sandwiched between two used periods.
        """
        for school_class in self.classes:
            for day in WEEKDAYS:
                used = {
                    period: self._used_var(school_class.id, f"{day}{period}")
                    for period in REGULAR_PERIODS
                }

                for i, period in enumerate(REGULAR_PERIODS):
                    before = REGULAR_PERIODS[:i]
                    after = REGULAR_PERIODS[i + 1 :]
                    if not before or not after:
                        continue  # first/last period of the day may always be free

                    any_before = self.model.NewBoolVar(f"any_before_{school_class.id}_{day}{period}")
                    self.model.AddMaxEquality(any_before, [used[p] for p in before])

                    any_after = self.model.NewBoolVar(f"any_after_{school_class.id}_{day}{period}")
                    self.model.AddMaxEquality(any_after, [used[p] for p in after])

                    # If there's a used period both before and after this one, it
                    # cannot be free.
                    self.model.Add(used[period] >= any_before + any_after - 1)

    def solve(self) -> dict[str, dict[str, tuple[str, str]]] | None:
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None

        schedule: dict[str, dict[str, tuple[str, str]]] = {}
        for (teacher_id, class_id, subject, slot), var in self.assign.items():
            if solver.Value(var) == 1:
                schedule.setdefault(class_id, {})[slot] = (subject, teacher_id)

        self.subject_shortfall = {
            key: solver.Value(var)
            for key, var in self.shortfall.items()
            if solver.Value(var) > 0
        }

        return schedule
