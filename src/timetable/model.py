"""
Create data models for teachers, classes, subjects, time slots, (rooms, ...?).
"""

# example of a teacher 
@dataclass
class Teacher:
    name: str
    subjects: list[str]
    availability: set[int]
