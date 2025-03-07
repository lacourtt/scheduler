from schedule_generator import Patient, Therapist, HourSlot, WeekDay, create_schedule

def float_to_time(f):
    """Convert a float time to a string in HH:MM format."""
    hour = int(f)
    minute = int((f - hour) * 60)
    return f"{hour:02d}:{minute:02d}"

def print_consultations(schedule, timeslots):
    """Print consultations for each patient, showing their schedule across the week."""
    # Extract unique patients from the schedule
    patients = set(p for p, _, _ in schedule)
    
    # Get list of weekdays from WeekDay enum
    days = [day.value for day in WeekDay]
    
    # Function to convert float time to string (e.g., 8.0 -> "08:00")
    def time_to_str(time_float):
        hour = int(time_float)
        minute = "00"
        return f"{hour:02d}:{minute}"
    
    # Iterate through each patient
    for patient in sorted(patients, key=lambda p: p.id):
        print(f"\n{patient.name} consultations:")
        
        # Group consultations by day for this patient
        consultations_by_day = {day: [] for day in days}
        for p, t, ts in schedule:
            if p == patient:
                day = ts["day_of_week"]
                start_time = time_to_str(ts["start_time"])
                end_time = time_to_str(ts["end_time"])
                consultations_by_day[day].append(f"{t.name} - {start_time} - {end_time}")
        
        # Print consultations for each day
        for day in days:
            if consultations_by_day[day]:
                for consultation in consultations_by_day[day]:
                    print(f"{day} - {consultation}")
            else:
                print(f"{day} - Free")

def print_schedule_table(schedule, timeslots):
    """Print a separate schedule table for each patient, showing their consultations across the week."""
    # Define the days of the week
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Extract unique time intervals from timeslots and sort by start time
    time_intervals = sorted(
        set((ts["start_time"], ts["end_time"]) for ts in timeslots),
        key=lambda x: x[0]
    )
    
    # Extract unique patients from the schedule
    patients = set(p for p, _, _ in schedule)
    
    # Iterate through each patient
    for patient in sorted(patients, key=lambda p: p.id):
        print(f"\nSchedule for {patient.name}:")
        
        # Initialize an empty schedule dictionary for this patient
        schedule_dict = {day: {interval: "Free" for interval in time_intervals} for day in days}
        
        # Populate the schedule dictionary with consultations for this patient
        for p, t, ts in schedule:
            if p == patient:
                day = ts["day_of_week"]
                start_time = ts["start_time"]
                end_time = ts["end_time"]
                interval = (start_time, end_time)
                schedule_dict[day][interval] = f"{t.name} ({get_initials(t.specialty)})"
        
        # Print the table header
        header = ["Time".ljust(12)] + [day.ljust(20) for day in days]
        print(" | ".join(header))
        print("-" * (12 + 22 * len(days)))  # Separator line
        
        # Print each row of the table
        for start, end in time_intervals:
            time_str = f"{int(start):02d}:{int((start % 1) * 60):02d} - {int(end):02d}:{int((end % 1) * 60):02d}"
            row = [time_str.ljust(12)]
            for day in days:
                row.append(schedule_dict[day][(start, end)].ljust(20))
            print(" | ".join(row))

def get_initials(text):
  """Extracts and returns the capital letters from a string."""
  initials = ""
  for char in text:
    if char.isupper():
      initials += char
  return initials

if __name__ == "__main__":
    # Define availability in terms of HalfHour enums
    morning_half_hours = [
        HourSlot._9to10,HourSlot._10to11, HourSlot._11to12
    ]
    morning_half_hours_2 = [
        HourSlot._9to10, HourSlot._10to11, HourSlot._11to12
    ]
    
    # Define sample timeslots (Monday and Tuesday, 9:00-12:00)
    timeslots = [
        {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 10.0},
        {"id": "2", "day_of_week": "Monday", "start_time": 10.0, "end_time": 11.0},
        {"id": "3", "day_of_week": "Monday", "start_time": 11.0, "end_time": 12.0},
        {"id": "4", "day_of_week": "Tuesday", "start_time": 9.0, "end_time": 10.0},
        {"id": "5", "day_of_week": "Tuesday", "start_time": 10.0, "end_time": 11.0},
        {"id": "6", "day_of_week": "Tuesday", "start_time": 11.0, "end_time": 12.0},
    ]
    
    # Define a patient
    patient_availability = {
        "Monday": morning_half_hours,
        "Tuesday": morning_half_hours_2,
    }
    therapist_availability = {
        "Monday": morning_half_hours,
        "Tuesday": morning_half_hours,
    }
    patient = Patient(
        id="P1",
        name="John Doe",
        weekly_specialty_needs={"Speech Therapist": 2},
        availability=patient_availability
    )
    
    # Define a therapist
    therapist = Therapist(
        id="T1",
        name="Dr. Smith",
        specialty="Speech Therapist",
        availability=therapist_availability
    )
    
    # Generate the schedule
    schedule = create_schedule([patient], [therapist], timeslots)
    
    # Print the table if a schedule is generated
    if schedule:
        print_schedule_table(schedule, timeslots)
    else:
        print("No schedule could be created.")