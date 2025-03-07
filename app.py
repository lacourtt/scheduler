from flask import Flask, render_template, request, redirect, url_for
from schedule_generator import HourSlot, WeekDay, Patient, Therapist, create_schedule
from print_table import print_schedule_table  # Assuming this is your module

app = Flask(__name__)

# In-memory cache for patients and therapists
patients_cache = []
therapists_cache = []

# Time slots for scheduling (7:00 to 18:00 in one-hour increments)
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

def parse_availability(text):
    """Parse availability text into a dictionary of day: [HourSlot] pairs."""
    availability = {}
    lines = text.split("\n")
    for line in lines:
        if ":" in line:
            day, times = line.split(":", 1)
            day = day.strip()
            if day not in [d.value for d in WeekDay]:
                continue
            time_list = [t.strip() for t in times.split(",")]
            hour_slots = []
            for time in time_list:
                try:
                    hour = int(time.split(":")[0])
                    if time == f"{hour:02d}:00" and 7 <= hour <= 17:
                        slot_name = f"_{hour}to{hour+1}"
                        hour_slots.append(getattr(HourSlot, slot_name))
                except (ValueError, AttributeError):
                    continue
            if hour_slots:
                availability[day] = hour_slots
    return availability

@app.route('/', methods=['GET', 'POST'])
def home():
    global patients_cache, therapists_cache
    status = ""
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_patient':
            name = request.form.get('patient_name')
            speech_hours = request.form.get('speech_hours', '0')
            psycho_hours = request.form.get('psycho_hours', '0')
            occ_hours = request.form.get('occ_hours', '0')
            availability = request.form.get('patient_availability')
            
            if not name or not availability:
                status = "Error: Patient name and availability are required!"
            else:
                try:
                    speech = int(speech_hours)
                    psycho = int(psycho_hours)
                    occ = int(occ_hours)
                    patient = Patient(
                        id=f"P{len(patients_cache) + 1}",
                        name=name,
                        weekly_specialty_needs={
                            "Speech Therapist": speech,
                            "Psychologist": psycho,
                            "Occupational Therapist": occ
                        },
                        availability=parse_availability(availability)
                    )
                    patients_cache.append(patient)
                    status = f"Added patient: {name}"
                except ValueError:
                    status = "Error: Hours must be integers!"
        
        elif action == 'add_therapist':
            name = request.form.get('therapist_name')
            specialty = request.form.get('specialty')
            availability = request.form.get('therapist_availability')
            
            if not name or not specialty or not availability:
                status = "Error: Therapist name, specialty, and availability are required!"
            else:
                therapist = Therapist(
                    id=f"T{len(therapists_cache) + 1}",
                    name=name,
                    specialty=specialty,
                    availability=parse_availability(availability)
                )
                therapists_cache.append(therapist)
                status = f"Added therapist: {name} ({specialty})"
        
        elif action == 'delete_patient':
            patient_id = request.form.get('patient_id')
            patients_cache[:] = [p for p in patients_cache if p.id != patient_id]
            status = f"Deleted patient with ID: {patient_id}"
        
        elif action == 'delete_therapist':
            therapist_id = request.form.get('therapist_id')
            therapists_cache[:] = [t for t in therapists_cache if t.id != therapist_id]
            status = f"Deleted therapist with ID: {therapist_id}"
        
        elif action == 'run_scheduler':
            if not patients_cache or not therapists_cache:
                status = "Error: Add at least one patient and one therapist!"
            else:
                schedule = create_schedule(patients_cache, therapists_cache, timeslots)
                if schedule:
                    import io
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = buffer = io.StringIO()
                    print_schedule_table(schedule, timeslots)
                    sys.stdout = old_stdout
                    schedule_output = buffer.getvalue()
                    return render_template('schedule.html', schedule_output=schedule_output)
                else:
                    status = "Error: No feasible schedule could be created."
    
    return render_template('index.html', status=status, patients=patients_cache, therapists=therapists_cache)

if __name__ == '__main__':
    app.run(debug=True)