import pytest
from schedule_generator import HalfHour, Patient, Therapist, WeekDay, create_schedule

# Test 1: Single patient and therapist with sufficient availability
def test_single_patient_single_therapist():
    # Setup: Patient needs 1 hour (2 consultations), both available Monday 9:00-10:00
    availability = {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}
    patient = Patient(
        id="P1",
        name="Patient 1",
        weekly_specialty_needs={"Speech Therapist": 1},  # 2 consultations
        availability=availability
    )
    therapist = Therapist(
        id="T1",
        name="Dr. Alice",
        specialty="Speech Therapist",
        availability=availability
    )
    timeslots = [
        {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
        {"id": "2", "day_of_week": "Monday", "start_time": 9.5, "end_time": 10.0},
    ]

    # Run scheduler
    schedule = create_schedule([patient], [therapist], timeslots)

    # Assertions
    assert schedule is not None, "Schedule should be feasible"
    assert len(schedule) == 2, f"Expected 2 consultations, got {len(schedule)}"
    scheduled_times = sorted([ts["start_time"] for p, t, ts in schedule])
    assert scheduled_times == [9.0, 9.5], "Consultations should be at 9:00 and 9:30"
    for p, t, ts in schedule:
        assert p.id == "P1", "Wrong patient scheduled"
        assert t.id == "T1", "Wrong therapist scheduled"

# Test 2: No overlapping availability (infeasible schedule)
def test_impossible_schedule():
    # Setup: Patient available Monday, therapist Tuesday
    patient = Patient(
        id="P1",
        name="Patient 1",
        weekly_specialty_needs={"Speech Therapist": 0.5},  # 1 consultation
        availability={"Monday": [HalfHour._9to9_30]}
    )
    therapist = Therapist(
        id="T1",
        name="Dr. Alice",
        specialty="Speech Therapist",
        availability={"Tuesday": [HalfHour._9to9_30]}
    )
    timeslots = [
        {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
        {"id": "2", "day_of_week": "Tuesday", "start_time": 9.0, "end_time": 9.5},
    ]

    # Run scheduler
    schedule = create_schedule([patient], [therapist], timeslots)

    # Assertion
    assert schedule is None, "Schedule should be infeasible due to no overlapping availability"

# Test 3: Prevent double-booking with limited timeslots
def test_no_double_booking():
    # Setup: Two patients, one therapist, one timeslot
    availability = {"Monday": [HalfHour._9to9_30]}
    patient1 = Patient(
        id="P1",
        name="Patient 1",
        weekly_specialty_needs={"Speech Therapist": 0.5},  # 1 consultation
        availability=availability
    )
    patient2 = Patient(
        id="P2",
        name="Patient 2",
        weekly_specialty_needs={"Speech Therapist": 0.5},  # 1 consultation
        availability=availability
    )
    therapist = Therapist(
        id="T1",
        name="Dr. Alice",
        specialty="Speech Therapist",
        availability=availability
    )
    timeslots = [
        {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
    ]

    # Run scheduler
    schedule = create_schedule([patient1, patient2], [therapist], timeslots)

    # Assertion
    assert schedule is None, "Schedule should be infeasible due to insufficient timeslots"

# Test 4: Multiple days with sufficient availability
def test_multiple_days():
    # Setup: Patient needs 1 hour (2 consultations), available Monday and Tuesday
    availability = {
        "Monday": [HalfHour._9to9_30],
        "Tuesday": [HalfHour._9to9_30]
    }
    patient = Patient(
        id="P1",
        name="Patient 1",
        weekly_specialty_needs={"Speech Therapist": 1},  # 2 consultations
        availability=availability
    )
    therapist = Therapist(
        id="T1",
        name="Dr. Alice",
        specialty="Speech Therapist",
        availability=availability
    )
    timeslots = [
        {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
        {"id": "2", "day_of_week": "Tuesday", "start_time": 9.0, "end_time": 9.5},
    ]

    # Run scheduler
    schedule = create_schedule([patient], [therapist], timeslots)

    # Assertions
    assert schedule is not None, "Schedule should be feasible"
    assert len(schedule) == 2, f"Expected 2 consultations, got {len(schedule)}"
    days_scheduled = set(ts["day_of_week"] for p, t, ts in schedule)
    assert days_scheduled.issubset({"Monday", "Tuesday"}), "Consultations on wrong days"
    for p, t, ts in schedule:
        assert ts["start_time"] == 9.0, "Wrong timeslot scheduled"

# Test 5: Multiple patients and therapists with overlapping needs
def test_multiple_patients_therapists():
    # Setup: Two patients, two therapists, limited overlapping availability
    patient1 = Patient(
        id="P1",
        name="Patient 1",
        weekly_specialty_needs={"Psychologist": 0.5},  # 1 consultation
        availability={"Monday": [HalfHour._9to9_30]}
    )
    patient2 = Patient(
        id="P2",
        name="Patient 2",
        weekly_specialty_needs={"Psychologist": 0.5},  # 1 consultation
        availability={"Monday": [HalfHour._9to9_30]}
    )
    therapist1 = Therapist(
        id="T1",
        name="Dr. Bob",
        specialty="Psychologist",
        availability={"Monday": [HalfHour._9to9_30]}
    )
    therapist2 = Therapist(
        id="T2",
        name="Dr. Carol",
        specialty="Psychologist",
        availability={"Monday": [HalfHour._9to9_30]}
    )
    timeslots = [
        {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
    ]

    # Run scheduler
    schedule = create_schedule([patient1, patient2], [therapist1, therapist2], timeslots)

    # Assertions
    assert schedule is not None, "Schedule should be feasible"
    assert len(schedule) == 2, f"Expected 2 consultations, got {len(schedule)}"
    patients_scheduled = set(p.id for p, t, ts in schedule)
    assert patients_scheduled == {"P1", "P2"}, "Both patients should be scheduled"
    therapists_scheduled = set(t.id for p, t, ts in schedule)
    assert therapists_scheduled.issubset({"T1", "T2"}), "Wrong therapists scheduled"