"""Sample notes so the app can be demoed in one click."""

SAMPLE_NOTES = [
    {"title": "Physics - Newton's laws", "tags": ["physics", "exam"], "pinned": True,
     "content": "1st: objects keep moving unless a force acts.\n2nd: F = m * a.\n3rd: every action has an equal and opposite reaction."},
    {"title": "Python list comprehensions", "tags": ["python", "coding"],
     "content": "squares = [x * x for x in range(10) if x % 2 == 0]\nFaster and shorter than a normal for loop for simple cases."},
    {"title": "Hackathon checklist", "tags": ["hackathon", "todo"], "pinned": True,
     "content": "- finish README\n- run all tests\n- record a 2 minute demo\n- zip the project"},
    {"title": "Maths - integration by parts", "tags": ["maths", "exam"],
     "content": "integral(u dv) = u*v - integral(v du). Choose u using LIATE."},
    {"title": "Library books to return", "tags": ["personal", "todo"],
     "content": "Return 'Clean Code' and 'Introduction to Algorithms' by Friday."},
    {"title": "Project idea: study planner", "tags": ["ideas", "coding"],
     "content": "Small app that turns exam dates into a daily revision schedule."},
]
