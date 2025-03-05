import unittest
from schedule_generator import Patient, Therapist, HalfHour, create_schedule

class TestScheduleGenerator(unittest.TestCase):
    def setUp(self):
        # Define time slots (1-hour each)
        self.monday_9_to_10 = {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 10.0}
        self.monday_10_to_11 = {"id": "2", "day_of_week": "Monday", "start_time": 10.0, "end_time": 11.0}
        self.monday_11_to_12 = {"id": "3", "day_of_week": "Monday", "start_time": 11.0, "end_time": 12.0}

        # Correct availability format: dict with day -> list of HalfHour
        patient_availability = {
            "Monday": [HalfHour._9to9_30, HalfHour._9_30to10, HalfHour._10to10_30, HalfHour._10_30to11]
        }
        therapist_availability = {
            "Monday": [HalfHour._9to9_30, HalfHour._9_30to10, HalfHour._10to10_30, HalfHour._10_30to11]
        }

        self.patient = Patient(
            id="P1",
            name="John Doe",
            weekly_specialty_needs={"Speech Therapist": 2, "Psychologist": 0, "Occupational Therapist": 0},
            availability=patient_availability
        )

        self.therapist = Therapist(
            id="T1",
            name="Dr. Smith",
            specialty="Speech Therapist",
            availability=therapist_availability
        )

        self.timeslots = [self.monday_9_to_10, self.monday_10_to_11]

    def test_patient_availability(self):
        schedule = create_schedule([self.patient], [self.therapist], self.timeslots)
        self.assertIsNotNone(schedule)
        self.assertEqual(len(schedule), 2)
        self.assertEqual(schedule[0][0].id, "P1")
        self.assertEqual(schedule[0][1].id, "T1")
        self.assertEqual(schedule[1][0].id, "P1")
        self.assertEqual(schedule[1][1].id, "T1")   

    def test_therapist_availability(self):
        unavailable_timeslot = [self.monday_11_to_12]
        schedule = create_schedule([self.patient], [self.therapist], unavailable_timeslot)
        self.assertIsNone(schedule)  # No availability at 11-12

    def test_double_booking_patient(self):
        limited_availability = {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}
        patient = Patient(
            id="P1",
            name="John Doe",
            weekly_specialty_needs={"Speech Therapist": 2},
            availability=limited_availability
        )
        timeslots = [self.monday_9_to_10]
        schedule = create_schedule([patient], [self.therapist], timeslots)
        self.assertIsNone(schedule)  # Only one slot available, need two

    def test_double_booking_therapist(self):
        limited_availability = {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}
        therapist = Therapist(
            id="T1",
            name="Dr. Smith",
            specialty="Speech Therapist",
            availability=limited_availability
        )
        timeslots = [self.monday_9_to_10]
        schedule = create_schedule([self.patient], [therapist], timeslots)
        self.assertIsNone(schedule)  # Therapist available for one slot only

    def test_meet_weekly_needs(self):
        schedule = create_schedule([self.patient], [self.therapist], self.timeslots)
        self.assertIsNotNone(schedule)
        self.assertEqual(len(schedule), 2)
        scheduled_times = [ts["id"] for p, t, ts in schedule]
        self.assertCountEqual(scheduled_times, ["1", "2"])  # Should use both slots

if __name__ == '__main__':
    unittest.main()