"""
Solve problem with OR-tools, Define Constraints, (export solutions?) -> NO EXCEL DEPENDENCIES!!!!
"""
from ortools.sat.python import cp_model
from timetable.model import Teacher


class TimetableSolver:
    def __init__(self, teachers: list[Teacher], time_slots: list[str]):
        self.teachers = teachers
        self.time_slots = time_slots
        self.model = cp_model.CpModel()
        self.x = {}  # Entscheidungsvariablen

    def build_model(self):
        """
        Create decision variables and constraints
            - swimming only noon due to swimming gym -> if class a has swimming then class b should have sport in the noon so we can switch them easily
            - only one class at once in the gym
            - find more...
        """

        # Decision variables:
        # x[(teacher_id, timeslot)] = 1, if teacher gives this lesson
        for teacher in self.teachers:
            for t in self.time_slots:
                self.x[(teacher.id, t)] = self.model.NewBoolVar(
                    f"x_{teacher.id}_{t}"
                )

        # Constraint: Teachers only in slots that they are avaiable
        for teacher in self.teachers:
            for t in self.time_slots:
                if t not in teacher.availability:
                    self.model.Add(self.x[(teacher.id, t)] == 0)

        # Constraint: max weekly hours
        for teacher in self.teachers:
            self.model.Add(
                sum(self.x[(teacher.id, t)] for t in self.time_slots)
                <= teacher.max_weekly_hours
            )

        # every slot needs to be taken 
        # TODO later this needs changing to prioritise core hours but can deviate from them if needed
        for slot in self.time_slots:
            self.model.Add(
                sum(self.x[(teacher.id, slot)] for teacher in self.teachers) >= 1
            )

    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None

        result = {}
        for (teacher_id, t), var in self.x.items():
            if solver.Value(var) == 1:
                result.setdefault(teacher_id, []).append(t)

        return result
