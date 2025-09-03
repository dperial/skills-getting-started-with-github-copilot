"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import re
from datetime import datetime, timedelta

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Basketball Team": {
        "description": "Join the school basketball team and compete in local leagues",
        "schedule": "Wednesdays, 4:00 PM - 6:00 PM",
        "max_participants": 15,
        "participants": ["alex@mergington.edu", "jordan@mergington.edu"]
    },
    "Soccer Club": {
        "description": "Practice soccer skills and play friendly matches",
        "schedule": "Saturdays, 10:00 AM - 12:00 PM",
        "max_participants": 20,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Art Workshop": {
        "description": "Explore painting, drawing, and sculpture techniques",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["ava@mergington.edu", "liam@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce school plays and performances",
        "schedule": "Mondays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["ella@mergington.edu", "noah@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["oliver@mergington.edu", "isabella@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging math problems and prepare for competitions",
        "schedule": "Fridays, 2:00 PM - 3:30 PM",
        "max_participants": 16,
        "participants": ["ethan@mergington.edu", "charlotte@mergington.edu"]
    },
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


def parse_schedule(schedule_str):
    """
    Parse le texte du planning et retourne une liste de tuples (jour, heure_debut, heure_fin)
    Exemple : "Wednesdays, 4:00 PM - 6:00 PM" -> [("Wednesday", 16:00, 18:00)]
    """
    days_map = {
        "Mondays": "Monday", "Tuesdays": "Tuesday", "Wednesdays": "Wednesday",
        "Thursdays": "Thursday", "Fridays": "Friday", "Saturdays": "Saturday", "Sundays": "Sunday"
    }
    results = []
    # Sépare les jours multiples
    parts = schedule_str.split(", ")
    days_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else ""
    # Gère les jours multiples
    days = [d.strip() for d in days_part.split(" and ")]
    # Gère les horaires
    time_match = re.match(r"(\d{1,2}:\d{2} [APM]{2}) - (\d{1,2}:\d{2} [APM]{2})", time_part)
    if time_match:
        start_str, end_str = time_match.groups()
        start_dt = datetime.strptime(start_str, "%I:%M %p")
        end_dt = datetime.strptime(end_str, "%I:%M %p")
        for day in days:
            results.append((days_map.get(day, day), start_dt.time(), end_dt.time()))
    else:
        # Cas où il y a plusieurs jours et horaires (ex: "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM")
        multi_days = [d.strip() for d in days_part.split(",")]
        if len(parts) > 1:
            time_match = re.match(r"(\d{1,2}:\d{2} [APM]{2}) - (\d{1,2}:\d{2} [APM]{2})", parts[1])
            if time_match:
                start_str, end_str = time_match.groups()
                start_dt = datetime.strptime(start_str, "%I:%M %p")
                end_dt = datetime.strptime(end_str, "%I:%M %p")
                for day in multi_days:
                    results.append((days_map.get(day, day), start_dt.time(), end_dt.time()))
    return results


def schedules_collide(schedule1, schedule2):
    """
    Vérifie si deux plannings se chevauchent
    """
    slots1 = parse_schedule(schedule1)
    slots2 = parse_schedule(schedule2)
    for day1, start1, end1 in slots1:
        for day2, start2, end2 in slots2:
            if day1 == day2:
                # Chevauchement d'horaires
                if start1 < end2 and start2 < end1:
                    return True
    return False


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity, checking for schedule collisions"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")

    # Vérifier les chevauchements d'horaires
    for other_name, other_activity in activities.items():
        if other_name == activity_name:
            continue
        if email in other_activity["participants"]:
            if schedules_collide(activity["schedule"], other_activity["schedule"]):
                raise HTTPException(
                    status_code=400,
                    detail=f"Impossible d'inscrire {email} à {activity_name} : les horaires chevauchent avec {other_name}."
                )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}
