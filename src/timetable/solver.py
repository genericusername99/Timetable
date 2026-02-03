"""
Solve problem with OR-tools, Define Constraints, (export solutions?) -> NO EXCEL DEPENDENCIES!!!!
"""
from ortools.sat.python import cp_model
from timetable.model import Teacher


class TimetableSolver:
    def __init__(self, teachers: list[Teacher], time_slots: list[int]):
        self.teachers = teachers
        self.time_slots = time_slots
        self.model = cp_model.CpModel()
        self.x = {}  # Entscheidungsvariablen

    def build_model(self):
        """
        Erstellt die Entscheidungsvariablen und Constraints
        """

        # Entscheidungsvariablen:
        # x[(teacher_id, timeslot)] = 1, wenn Lehrer in diesem Slot unterrichtet
        for teacher in self.teachers:
            for t in self.time_slots:
                self.x[(teacher.id, t)] = self.model.NewBoolVar(
                    f"x_{teacher.id}_{t}"
                )

        # Constraint 1: Jeder Lehrer unterrichtet GENAU 1 Stunde (POC!)
        for teacher in self.teachers:
            self.model.Add(
                sum(self.x[(teacher.id, t)] for t in self.time_slots) == 1
            )

        # Constraint 2: Lehrer nur in verfügbaren Slots
        for teacher in self.teachers:
            for t in self.time_slots:
                if t not in teacher.availability:
                    self.model.Add(self.x[(teacher.id, t)] == 0)

        # Constraint 3: Max. Wochenstunden (hier trivial, aber wichtig)
        for teacher in self.teachers:
            self.model.Add(
                sum(self.x[(teacher.id, t)] for t in self.time_slots)
                <= teacher.max_weekly_hours
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
