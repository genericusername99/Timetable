# src/timetable/constants.py

WEEKDAYS = ["Mo", "Di", "Mi", "Do", "Fr"]
PERIODS = [1, 2, 3, 4, 5, 6]
AFTERNOON = "NU"

# TIME_SLOTS global auf Modulebene definieren
TIME_SLOTS = [f"{day}{p}" for day in WEEKDAYS for p in PERIODS]
TIME_SLOTS += [f"{day}{AFTERNOON}" for day in WEEKDAYS]
