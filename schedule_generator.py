from enum import Enum
from ortools.sat.python import cp_model
from typing import List, Dict
import random

class HourSlot(Enum):
    """Represents operating hours from 7 AM to 6 PM in one-hour increments."""
    _7to8 = "07:00 - 08:00"
    _8to9 = "08:00 - 09:00"
    _9to10 = "09:00 - 10:00"
    _10to11 = "10:00 - 11:00"
    _11to12 = "11:00 - 12:00"
    _12to13 = "12:00 - 13:00"
    _13to14 = "13:00 - 14:00"
    _14to15 = "14:00 - 15:00"
    _15to16 = "15:00 - 16:00"
    _16to17 = "16:00 - 17:00"
    _17to18 = "17:00 - 18:00"

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
        self.availability = availability  # e.g., {"Monday": [HourSlot._9to10, HourSlot._10to11]}

class Therapist:
    """Represents a therapist with a specialty and availability."""
    def __init__(self, id: str, name: str, specialty: str, availability: dict):
        self.id = id
        self.name = name
        self.specialty = specialty
        self.availability = availability  # e.g., {"Monday": [HourSlot._9to10, HourSlot._10to11]}

class Consultation:
    """Represents a scheduled consultation."""
    def __init__(self, id: str, patient: Patient, therapist: Therapist, timeslot: dict):
        self.id = id
        self.patient = patient
        self.therapist = therapist
        self.timeslot = timeslot  # e.g., {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 10.0}

def get_hour_slot(start_time: float) -> HourSlot:
    """Returns the HourSlot corresponding to a timeslot's start time."""
    hour = int(start_time)
    slot_name = f"_{hour}to{hour+1}"
    return getattr(HourSlot, slot_name)

def create_schedule(patients: List[Patient], therapists: List[Therapist], timeslots: List[dict]) -> List[tuple]:
    model = cp_model.CpModel()

    # We use these weights for the soft rules.
    bonus_weight = 1              # bonus for any consecutive appointment
    same_bonus_weight = 1         # bonus for consecutive appointments with the same therapist

    # Create consultation decision variables.
    consultations = []
    for patient in patients:
        for therapist in therapists:
            if therapist.specialty in patient.weekly_specialty_needs and patient.weekly_specialty_needs[therapist.specialty] > 0:
                for timeslot in timeslots:
                    var_name = f'consultation_{patient.id}_{therapist.id}_{timeslot["id"]}'
                    consultation = model.NewBoolVar(var_name)
                    consultations.append((consultation, patient, therapist, timeslot))

    # Enforce availability: if a patient or therapist is not available in a given timeslot, force the variable to 0.
    for consultation, patient, therapist, timeslot in consultations:
        day = timeslot["day_of_week"]
        hour_slot = get_hour_slot(timeslot["start_time"])
        patient_available = hour_slot in patient.availability.get(day, [])
        therapist_available = hour_slot in therapist.availability.get(day, [])
        if not (patient_available and therapist_available):
            model.Add(consultation == 0)

    # Prevent double-booking: for each timeslot, a patient and a therapist can have at most one consultation.
    for timeslot in timeslots:
        for therapist in therapists:
            overlapping = [c for c, p, t, ts in consultations if t == therapist and ts == timeslot]
            model.Add(sum(overlapping) <= 1)
        for patient in patients:
            overlapping = [c for c, p, t, ts in consultations if p == patient and ts == timeslot]
            model.Add(sum(overlapping) <= 1)

    # Weekly needs constraints: each patient must have exactly the required number of consultations for each specialty.
    for patient in patients:
        for specialty, hours_needed in patient.weekly_specialty_needs.items():
            if hours_needed > 0:
                relevant_consultations = [c for c, p, t, ts in consultations if p == patient and t.specialty == specialty]
                if not relevant_consultations:
                    print(f"Warning: No consultations possible for {patient.name} with {specialty}")
                model.Add(sum(relevant_consultations) == hours_needed)

    # ***** Soft Constraint for Consecutive Appointments (regardless of therapist) *****
    # For each patient and each timeslot, create an auxiliary variable that indicates if a patient is scheduled.
    scheduled = {}  # key: (patient.id, timeslot["id"]) -> IntVar (0 or 1)
    for patient in patients:
        for ts in timeslots:
            var = model.NewIntVar(0, 1, f'scheduled_{patient.id}_{ts["id"]}')
            relevant = [c for c, p, t, ts_candidate in consultations if p == patient and ts_candidate == ts]
            if relevant:
                model.Add(var == sum(relevant))
            else:
                model.Add(var == 0)
            scheduled[(patient.id, ts["id"])] = var

    # Group timeslots by day.
    timeslots_by_day = {}
    for ts in timeslots:
        day = ts["day_of_week"]
        timeslots_by_day.setdefault(day, []).append(ts)
    for day, ts_list in timeslots_by_day.items():
        ts_list.sort(key=lambda x: x["start_time"])

    bonus_vars = []
    # For each patient and each day, for each adjacent pair of timeslots, create a bonus variable.
    for patient in patients:
        if any(day in patient.availability for day in timeslots_by_day):
            for day, ts_list in timeslots_by_day.items():
                if day not in patient.availability:
                    continue
                for i in range(len(ts_list) - 1):
                    ts1 = ts_list[i]
                    ts2 = ts_list[i+1]
                    bonus_var = model.NewIntVar(0, 1, f'bonus_{patient.id}_{ts1["id"]}_{ts2["id"]}')
                    s1 = scheduled[(patient.id, ts1["id"])]
                    s2 = scheduled[(patient.id, ts2["id"])]
                    model.Add(bonus_var <= s1)
                    model.Add(bonus_var <= s2)
                    model.Add(bonus_var >= s1 + s2 - 1)
                    bonus_vars.append(bonus_var)

    # ***** Soft Constraint for Consecutive Appointments with the Same Therapist *****
    # Create a helper dictionary for fast lookup: (patient.id, therapist.id, timeslot["id"]) -> consultation variable.
    consultation_dict = {}
    for c, p, t, ts in consultations:
        consultation_dict[(p.id, t.id, ts["id"])] = c

    same_therapist_bonus_vars = []
    # For each patient, each therapist, and each day, for every adjacent pair of timeslots,
    # add a bonus if both appointments with that therapist are scheduled.
    for patient in patients:
        for therapist in therapists:
            for day, ts_list in timeslots_by_day.items():
                # Only consider if the patient could be scheduled on that day.
                if day not in patient.availability:
                    continue
                for i in range(len(ts_list) - 1):
                    ts1 = ts_list[i]
                    ts2 = ts_list[i+1]
                    key1 = (patient.id, therapist.id, ts1["id"])
                    key2 = (patient.id, therapist.id, ts2["id"])
                    # Only add bonus if the consultation variables exist.
                    if key1 in consultation_dict and key2 in consultation_dict:
                        c1 = consultation_dict[key1]
                        c2 = consultation_dict[key2]
                        bonus_var = model.NewIntVar(0, 1, f'same_bonus_{patient.id}_{therapist.id}_{ts1["id"]}_{ts2["id"]}')
                        model.Add(bonus_var <= c1)
                        model.Add(bonus_var <= c2)
                        model.Add(bonus_var >= c1 + c2 - 1)
                        same_therapist_bonus_vars.append(bonus_var)

    # Modify the objective.
    # The sum over scheduled consultations is fixed by the hard constraints.
    # We add both bonus terms (with different weights) to softly prefer consecutive appointments and
    # consecutive appointments with the same therapist.
    model.Maximize(
        sum(c for c, p, t, ts in consultations) +
        bonus_weight * sum(bonus_vars) +
        same_bonus_weight * sum(same_therapist_bonus_vars)
    )

    # Solve the model.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(f"Solver status: {solver.StatusName(status)}")

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        schedule = []
        for consultation, patient, therapist, timeslot in consultations:
            if solver.Value(consultation):
                schedule.append((patient, therapist, timeslot))
        # Optional: Print bonus information.
        total_bonus = solver.Value(sum(bonus_vars)) if bonus_vars else 0
        total_same_bonus = solver.Value(sum(same_therapist_bonus_vars)) if same_therapist_bonus_vars else 0
        print(f"Total consecutive bonus: {total_bonus}")
        print(f"Total same-therapist consecutive bonus: {total_same_bonus}")

        # Verification (optional)
        for patient in patients:
            for specialty, hours_needed in patient.weekly_specialty_needs.items():
                if hours_needed > 0:
                    num_consultations = sum(1 for p, t, ts in schedule if p == patient and t.specialty == specialty)
                    expected = hours_needed
                    if num_consultations != expected:
                        print(f"Error: {patient.name} has {num_consultations} {specialty} consultations, needs {expected}")
                    else:
                        print(f"Verified: {patient.name} has {num_consultations} {specialty} consultations, matches {expected}")
        return schedule
    else:
        print("No feasible schedule found.")
        return None
