# Timetable
This project will use OR-Tools to solve the problem of creating a timetable for an elementary school. The project is set-up in Python and output the results in a excel sheet. Goal is to use compile the software to an .exe-file for easy use later on.

main.py

  ↓

excel_export.py     →       read excel

  ↓

model.py            →       envoke data structures

  ↓

solver.py           →       use OR-tools 

  ↓

excel_export.py     →       export results to excel


For execution always use "wsl" to start wsl in my powershell and then "source .venv/bin/activate" to activate the environment.

Tests can then be run by "pytest"

Application can be run by: "PYTHONPATH=src python -m timetable.main"
