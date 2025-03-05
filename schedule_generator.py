from enum import Enum
from ortools.sat.python import cp_model
from typing import List, Dict
import random

class HalfHour(Enum):
    """Represents operating hours from 6 AM to 7 PM in half-hour increments."""
    # Morning hours (6 AM - 12 PM)
    _6to6_30 = "06:00"
    _6_30to7 = "06:30"
    _7to7_30 = "07:00"
    _7_30to8 = "07:30"
    _8to8_30 = "08:00"
    _8_30to9 = "08:30"
    _9to9_30 = "09:00"
    _9_30to10 = "09:30"
    _10to10_30 = "10:00"
    _10_30to11 = "10:30"
    _11to11_30 = "11:00"
    _11_30to12 = "11:30"
    # Afternoon hours (12 PM - 7 PM)
    _12to12_30 = "12:00"
    _12_30to13 = "12:30"
    _13to13_30 = "13:00"
    _13_30to14 = "13:30"
    _14to14_30 = "14:00"
    _14_30to15 = "14:30"
    _15to15_30 = "15:00"
    _15_30to16 = "15:30"
    _16to16_30 = "16:00"
    _16_30to17 = "16:30"
    _17to17_30 = "17:00"
    _17_30to18 = "17:30"
    _18to18_30 = "18:00"
    _18_30to19 = "18:30"

class WeekDay(Enum):
    """Represents days of the week (Monday to Friday)."""
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"

class Patient:
    """Represents a patient with weekly specialty needs and availability."""
    def __init__(self, id: str, name: str, weekly_specialty_needs: dict, availability: dict):
        self.id = id
        self.name = name
        self.weekly_specialty_needs = weekly_specialty_needs  # e.g., {"Speech Therapist": 2}
        self.availability = availability  # e.g., {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}

class Therapist:
    """Represents a therapist with a specialty and availability."""
    def __init__(self, id: str, name: str, specialty: str, availability: dict):
        self.id = id
        self.name = name
        self.specialty = specialty
        self.availability = availability  # e.g., {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}

class Consultation:
    """Represents a scheduled consultation."""
    def __init__(self, id: str, patient: Patient, therapist: Therapist, timeslot: dict):
        self.id = id
        self.patient = patient
        self.therapist = therapist
        self.timeslot = timeslot  # e.g., {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5}

def get_half_hours_covered(timeslot: dict) -> list[HalfHour]:
    """Returns the list of HalfHour enums covered by a time slot."""
    start = timeslot["start_time"]  # e.g., 9.0
    end = timeslot["end_time"]      # e.g., 9.5 for a half-hour slot
    half_hours = []
    current = start
    while current < end:
        hour = int(current)
        minute = 0 if current == hour else 30
        time_str = f"{hour:02d}:{minute:02d}"
        for hh in HalfHour:
            if hh.value == time_str:
                half_hours.append(hh)
                break
        current += 0.5
    return half_hours

def create_schedule(patients: list[Patient], therapists: list[Therapist], timeslots: list[dict]) -> list[tuple]:
    model = cp_model.CpModel()

    # Create consultation variables
    consultations = []
    for patient in patients:
        for therapist in therapists:
            if therapist.specialty in patient.weekly_specialty_needs and patient.weekly_specialty_needs[therapist.specialty] > 0:
                for timeslot in timeslots:
                    var_name = f'consultation_{patient.id}_{therapist.id}_{timeslot["id"]}'
                    consultation = model.NewBoolVar(var_name)
                    consultations.append((consultation, patient, therapist, timeslot))

    # Availability constraints
    for consultation, patient, therapist, timeslot in consultations:
        day = timeslot["day_of_week"]
        covered_half_hours = get_half_hours_covered(timeslot)
        patient_available = all(hh in patient.availability.get(day, []) for hh in covered_half_hours)
        therapist_available = all(hh in therapist.availability.get(day, []) for hh in covered_half_hours)
        if not (patient_available and therapist_available):
            model.Add(consultation == 0)

    # No double-booking constraints
    for timeslot in timeslots:
        for therapist in therapists:
            overlapping = [c for c, p, t, ts in consultations if t == therapist and ts == timeslot]
            model.Add(sum(overlapping) <= 1)
        for patient in patients:
            overlapping = [c for c, p, t, ts in consultations if p == patient and ts == timeslot]
            model.Add(sum(overlapping) <= 1)

    # Weekly needs constraints
    for patient in patients:
        for specialty, hours_needed in patient.weekly_specialty_needs.items():
            if hours_needed > 0:
                relevant_consultations = [c for c, p, t, ts in consultations if p == patient and t.specialty == specialty]
                if not relevant_consultations:
                    print(f"Warning: No consultations possible for {patient.name} with {specialty}")
                model.Add(sum(relevant_consultations) == hours_needed * 2)

    # Objective
    model.Maximize(sum(c for c, p, t, ts in consultations))

    # Solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(f"Solver status: {solver.StatusName(status)}")

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule = []
        for consultation, patient, therapist, timeslot in consultations:
            if solver.Value(consultation):
                schedule.append((patient, therapist, timeslot))

        # Verify the schedule
        for patient in patients:
            for specialty, hours_needed in patient.weekly_specialty_needs.items():
                if hours_needed > 0:
                    num_consultations = sum(1 for p, t, ts in schedule if p == patient and t.specialty == specialty)
                    expected = hours_needed * 2
                    if num_consultations != expected:
                        print(f"Error: {patient.name} has {num_consultations} {specialty} consultations, needs {expected}")
                    else:
                        print(f"Verified: {patient.name} has {num_consultations} {specialty} consultations, matches {expected}")
        return schedule
    else:
        print("No feasible schedule found.")
        return None