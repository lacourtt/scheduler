import random
from typing import List
from schedule_generator import HourSlot  # Updated import
from csv_exporter import export_schedule_to_csv

# Assuming print_schedule_table is updated to work with one-hour timeslots
from schedule_generator import HourSlot, Patient, Therapist, WeekDay, create_schedule
from print_table import print_consultations, print_schedule_table

def create_hour_slots_for_range(start_hour: float, end_hour: float) -> List[HourSlot]:
    """
    Creates a list of HourSlot enums for a given time range.
    Args:
        start_hour: Start time (e.g., 7.0 for 7:00 AM).
        end_hour: End time (e.g., 18.0 for 6:00 PM).
    Returns:
        List of HourSlot enums covering the range.
    """
    hour_slots = []
    current = int(start_hour)
    while current < end_hour:
        slot_name = f"_{current}to{current+1}"
        hour_slots.append(getattr(HourSlot, slot_name))
        current += 1
    return hour_slots

def generate_varied_availability(start_hour: float = 7.0, end_hour: float = 18.0) -> dict[str, List[HourSlot]]:
    """
    Generates varied availability for a person across the week.
    Each day has a random block of available hours (at least 2 hours, up to full day).
    Args:
        start_hour: Operating start hour (e.g., 7.0 for 7 AM).
        end_hour: Operating end hour (e.g., 18.0 for 6 PM).
    Returns:
        Dict mapping day names to lists of available HourSlot slots.
    """
    availability = {}
    for day in WeekDay:
        # Decide if the person is available at all on this day (80% chance of being available)
        if random.random() < 0.2:
            availability[day.value] = []
            continue

        # Choose a random start and end time for availability (minimum 2 hours)
        possible_starts = list(range(int(start_hour), int(end_hour) - 2))
        if not possible_starts:
            possible_starts = [int(start_hour)]
        start = random.choice(possible_starts)
        min_end = min(start + 2, int(end_hour))
        max_end = int(end_hour)
        end = random.randint(min_end, max_end)

        # Generate one-hour slots for this range
        hour_slots = create_hour_slots_for_range(float(start), float(end))
        availability[day.value] = hour_slots

    return availability

def create_complex_test_case():
    """
    Creates a complex test case with 4 therapists and 10 patients with varied availability.
    Returns:
        Tuple of (patients, therapists, timeslots).
    """
    # Define therapists with varied availability
    therapists = [
        Therapist(
            id="T1",
            name="Dr. Alice",
            specialty="Speech Therapist",
            availability=generate_varied_availability()
        ),
        Therapist(
            id="T2",
            name="Dr. Bob",
            specialty="Psychologist",
            availability=generate_varied_availability()
        ),
        Therapist(
            id="T3",
            name="Dr. Charlie",
            specialty="Occupational Therapist",
            availability=generate_varied_availability()
        ),
        Therapist(
            id="T4",
            name="Dr. Dana",
            specialty="Speech Therapist",
            availability=generate_varied_availability()
        ),
    ]

    # Define patients with varied weekly needs and availability
    patients = []
    for i in range(1, 11):
        # Randomly assign needs (0 to 3 hours per specialty)
        needs = {
            "Speech Therapist": random.randint(0, 3),
            "Psychologist": random.randint(0, 3),
            "Occupational Therapist": random.randint(0, 3)
        }
        # Ensure at least some need to avoid trivial cases
        while sum(needs.values()) == 0:
            needs[random.choice(list(needs.keys()))] = random.randint(1, 3)

        # Adjust needs based on availability to increase likelihood of a feasible schedule
        patient_availability = generate_varied_availability()
        total_available_hours = sum(len(hour_slots) for hour_slots in patient_availability.values())  # Each slot is 1 hour
        total_needs = sum(needs.values())
        if total_needs > total_available_hours:
            # Scale down needs proportionally to fit availability
            factor = total_available_hours / total_needs if total_needs > 0 else 1
            for specialty in needs:
                needs[specialty] = int(needs[specialty] * factor)
            # Ensure at least some need remains
            if sum(needs.values()) == 0 and total_available_hours > 0:
                needs[random.choice(list(needs.keys()))] = 1

        patients.append(Patient(
            id=f"P{i}",
            name=f"Patient {i}",
            weekly_specialty_needs=needs,
            availability=patient_availability
        ))

    # Define time slots as one-hour blocks from 7:00 to 18:00, Monday to Friday.
    timeslots = []
    slot_id = 1
    for day in WeekDay:
        current = 7.0
        while current < 18.0:
            timeslots.append({
                "id": str(slot_id),
                "day_of_week": day.value,
                "start_time": current,
                "end_time": current + 1.0
            })
            slot_id += 1
            current += 1.0

    return patients, therapists, timeslots

if __name__ == "__main__":
    patients, therapists, timeslots = create_complex_test_case()

    print("Patients:")
    for p in patients:
        print(f"{p.name}: Needs={p.weekly_specialty_needs}")
        print("Availability:")
        for day, slots in p.availability.items():
            print(f"  {day}: {[slot.value for slot in slots]}")
    print("\nTherapists:")
    for t in therapists:
        print(f"{t.name} ({t.specialty}):")
        print("Availability:")
        for day, slots in t.availability.items():
            print(f"  {day}: {[slot.value for slot in slots]}")
    print(f"\nTotal Time Slots: {len(timeslots)}")

    # Generate the schedule
    schedule = create_schedule(patients, therapists, timeslots)

    # Print the table if a schedule is generated
    if schedule:
        print_consultations(schedule, timeslots)
        print_schedule_table(schedule, timeslots)
        export_schedule_to_csv(schedule, timeslots)
    else:
        print("No schedule could be created.")