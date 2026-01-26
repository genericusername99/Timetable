from enum import Enum

"""
Enum to hold different status of teaching personelle
"""
class TeacherRole(Enum):
    FULL = "full_teacher"
    PART_TIME = "part_time"
    EXTERNAL = "external"     # priest or similar
    SUBSTITUTE = "substitute"