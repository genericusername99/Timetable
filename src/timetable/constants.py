# src/timetable/constants.py

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr"]
PERIODS = [1, 2, 3, 4, 5, 6]
AFTERNOON = "NU"

# TIME_SLOTS global auf Modulebene definieren
TIME_SLOTS = [f"{day}{p}" for day in WEEKDAYS for p in PERIODS]
TIME_SLOTS += [f"{day}{AFTERNOON}" for day in WEEKDAYS]

# Weights for the solver's best-fit objective: how costly it is to leave a slot
# uncovered. Core periods should be filled before afternoon ("NU") blocks.
CORE_SLOT_WEIGHT = 5
AFTERNOON_SLOT_WEIGHT = 1
SLOT_WEIGHTS = {
    slot: (AFTERNOON_SLOT_WEIGHT if slot.endswith(AFTERNOON) else CORE_SLOT_WEIGHT)
    for slot in TIME_SLOTS
}
