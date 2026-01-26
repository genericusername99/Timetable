from dataclasses import dataclass
from timetable.enums.teacher_role import TeacherRole

"""
Create data models for teachers, classes, subjects, time slots, (rooms, ...?).
"""

# example structure of a teacher 
@dataclass
class Teacher:
    id: str
    name: str

    subjects: set[str]
    max_weekly_hours: int
    availability: set[int] # Define IDs (i.e. Mo1=0, Mo2=1, ...)
    
    role: TeacherRole
    
    is_homeroom_teacher: bool
    homeroom_class: str | None

# example structure of a class
@dataclass
class SchoolClass:
    id: str
    name: str

    number_of_students: int
    
    required_subjects: dict[str, int]  # subject -> weekly hours
