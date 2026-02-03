"""
Solve problem with OR-tools, Define Constraints, (export solutions?) -> NO EXCEL DEPENDENCIES!!!!
"""
from ortools.sat.python import cp_model

# create model
model = cp_model.CpModel()

# timeslots
time_slots = [1, 2, 3]

# variable: lesson in slot t?
x = {
    t: model.NewBoolVar(f"math_in_slot_{t}")
    for t in time_slots
}

# constraint 1: exactly one slot
model.Add(sum(x[t] for t in time_slots) == 1)

# constraint 2: teacher only avaiable in 1 and 3
availability = {1, 3}
for t in time_slots:
    if t not in availability:
        model.Add(x[t] == 0)

# solver
solver = cp_model.CpSolver()
status = solver.Solve(model)

# result
if status == cp_model.OPTIMAL:
    for t in time_slots:
        if solver.Value(x[t]) == 1:
            print(f"Mathe findet in Slot {t} statt")
else:
    print("Keine Lösung gefunden")
