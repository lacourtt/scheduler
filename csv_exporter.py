import csv

def export_schedule_to_csv(schedule, timeslots, output_dir="patient_schedules"):
    """
    Export each patient's schedule to a separate CSV file.
    
    Args:
        schedule: List of (patient, therapist, timeslot) tuples representing the schedule.
        timeslots: List of time slot dictionaries with 'start_time' and 'end_time'.
        output_dir: Directory to save CSV files (default: 'patient_schedules').
    """
    import os
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
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
        # Initialize an empty schedule dictionary for this patient
        schedule_dict = {day: {interval: "Free" for interval in time_intervals} for day in days}
        
        # Populate the schedule dictionary with consultations for this patient
        for p, t, ts in schedule:
            if p == patient:
                day = ts["day_of_week"]
                start_time = ts["start_time"]
                end_time = ts["end_time"]
                interval = (start_time, end_time)
                schedule_dict[day][interval] = f"{t.name} ({t.specialty})"
        
        # Define CSV file path (e.g., "patient_schedules/Patient_1_schedule.csv")
        csv_filename = os.path.join(output_dir, f"{patient.name.replace(' ', '_')}_schedule.csv")
        
        # Write to CSV
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header row
            header = ["Time"] + days
            writer.writerow(header)
            
            # Write data rows
            for start, end in time_intervals:
                time_str = f"{int(start):02d}:{int((start % 1) * 60):02d} - {int(end):02d}:{int((end % 1) * 60):02d}"
                row = [time_str]
                for day in days:
                    row.append(schedule_dict[day][(start, end)])
                writer.writerow(row)
        
        print(f"Exported schedule for {patient.name} to {csv_filename}")

# Example usage (add this after generating your schedule):
# schedule = create_schedule(patients, therapists, timeslots)
# if schedule:
#     export_schedule_to_csv(schedule, timeslots)