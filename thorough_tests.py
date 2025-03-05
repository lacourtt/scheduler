import unittest
import random

from complex_test_case import create_complex_test_case, create_half_hours_for_range, generate_varied_availability
from schedule_generator import HalfHour, Patient, Therapist, WeekDay, create_schedule, get_half_hours_covered

# Assume that the scheduling code is in a module called scheduling_module.
# For these tests, we import the relevant classes and functions:
#
# from scheduling_module import (
#     HalfHour, WeekDay, Patient, Therapist, get_half_hours_covered,
#     create_half_hours_for_range, generate_varied_availability, create_schedule,
#     create_complex_test_case
# )
#
# For demonstration purposes, we assume the scheduling code from the previous example is already available.

# In our tests below, we refer directly to the classes and functions as if they
# were imported. (In your actual test file, adjust the import paths accordingly.)

class TestScheduling(unittest.TestCase):

    def test_get_half_hours_covered_full_hour(self):
        """Test that a full hour time slot returns exactly two half-hour slots."""
        timeslot = {"start_time": 9.0, "end_time": 10.0}
        expected = [HalfHour._9to9_30, HalfHour._9_30to10]
        result = get_half_hours_covered(timeslot)
        self.assertEqual([hh.value for hh in result],
                         [hh.value for hh in expected],
                         "A full hour should cover two half-hour segments.")

    def test_get_half_hours_covered_half_hour(self):
        """Test that a half-hour time slot returns exactly one half-hour slot."""
        timeslot = {"start_time": 13.0, "end_time": 13.5}
        expected = [HalfHour._13to13_30]
        result = get_half_hours_covered(timeslot)
        self.assertEqual([hh.value for hh in result],
                         [hh.value for hh in expected],
                         "A half-hour time slot should return a single half-hour segment.")

    def test_create_half_hours_for_range(self):
        """Test that creating half-hour slots for a range returns the correct list."""
        result = create_half_hours_for_range(7.0, 9.0)
        expected = [HalfHour._7to7_30, HalfHour._7_30to8, HalfHour._8to8_30, HalfHour._8_30to9]
        self.assertEqual([hh.value for hh in result],
                         [hh.value for hh in expected],
                         "The half-hour range from 7:00 to 9:00 should be split into four segments.")

    def test_generate_varied_availability_structure(self):
        """Test that generated availability covers all weekdays and returns HalfHour enums."""
        random.seed(42)  # Set seed for reproducibility
        availability = generate_varied_availability(7.0, 18.0)
        expected_days = {day.value for day in WeekDay}
        self.assertEqual(set(availability.keys()), expected_days,
                         "Availability should have all weekdays as keys.")
        for day, slots in availability.items():
            for slot in slots:
                self.assertIsInstance(slot, HalfHour,
                                      "Each availability slot should be an instance of HalfHour.")

    def test_create_schedule_simple(self):
        """
        Create a simple scenario where a patient and a therapist are available for
        exactly two consecutive half-hour slots. The patient needs 1 hour (i.e. 2 sessions).
        """
        availability = {
            "Monday": [HalfHour._9to9_30, HalfHour._9_30to10],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": []
        }
        # Patient needs 1 hour (2 half-hour sessions) for Speech Therapy.
        patient = Patient(id="P1", name="Patient 1",
                          weekly_specialty_needs={"Speech Therapist": 1},
                          availability=availability)
        therapist = Therapist(id="T1", name="Dr. Alice", specialty="Speech Therapist",
                              availability=availability)
        # Create two time slots on Monday that exactly match the available half-hour blocks.
        timeslots = [
            {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
            {"id": "2", "day_of_week": "Monday", "start_time": 9.5, "end_time": 10.0}
        ]
        schedule = create_schedule([patient], [therapist], timeslots)
        self.assertIsNotNone(schedule, "A valid schedule should be found.")
        self.assertEqual(len(schedule), 2, "There should be exactly 2 consultations scheduled.")
        for entry in schedule:
            p, t, ts = entry
            self.assertEqual(ts["day_of_week"], "Monday")
            self.assertIn(ts["id"], ["1", "2"],
                          "The scheduled timeslot should be one of the provided ones.")

    def test_create_schedule_unsat_due_to_no_availability(self):
        """
        Test that if a patient has no availability for a needed specialty, the schedule
        cannot be created (i.e. returns None).
        """
        patient_availability = {"Monday": []}
        therapist_availability = {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}
        patient = Patient(id="P1", name="Patient 1",
                          weekly_specialty_needs={"Psychologist": 1},
                          availability=patient_availability)
        therapist = Therapist(id="T2", name="Dr. Bob", specialty="Psychologist",
                              availability=therapist_availability)
        timeslots = [
            {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
            {"id": "2", "day_of_week": "Monday", "start_time": 9.5, "end_time": 10.0}
        ]
        schedule = create_schedule([patient], [therapist], timeslots)
        self.assertIsNone(schedule, "The schedule should be unsatisfiable if the patient has no availability.")

    def test_create_schedule_no_timeslots(self):
        """Test that providing an empty list of timeslots results in no schedule (None)."""
        availability = {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}
        patient = Patient(id="P1", name="Patient 1",
                          weekly_specialty_needs={"Speech Therapist": 1},
                          availability=availability)
        therapist = Therapist(id="T1", name="Dr. Alice", specialty="Speech Therapist",
                              availability=availability)
        timeslots = []  # No available timeslots provided.
        schedule = create_schedule([patient], [therapist], timeslots)
        self.assertIsNone(schedule, "A schedule should not be created if there are no timeslots.")

    def test_patient_with_zero_needs(self):
        """
        If a patient has zero weekly needs for a given specialty, no consultation variables
        should be created, and the schedule should simply return an empty list.
        """
        availability = {"Monday": [HalfHour._9to9_30, HalfHour._9_30to10]}
        patient = Patient(id="P1", name="Patient 1",
                          weekly_specialty_needs={"Speech Therapist": 0},
                          availability=availability)
        therapist = Therapist(id="T1", name="Dr. Alice", specialty="Speech Therapist",
                              availability=availability)
        timeslots = [
            {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
            {"id": "2", "day_of_week": "Monday", "start_time": 9.5, "end_time": 10.0}
        ]
        schedule = create_schedule([patient], [therapist], timeslots)
        self.assertEqual(schedule, [],
                         "When a patient has zero needs, no consultations should be scheduled.")

    def test_weekly_needs_scaling(self):
        """
        Test that a patient needing 2 hours (i.e. 4 half-hour sessions) is scheduled for exactly 4 sessions.
        """
        availability = {
            "Monday": [HalfHour._9to9_30, HalfHour._9_30to10, HalfHour._10to10_30, HalfHour._10_30to11],
            "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": []
        }
        patient = Patient(id="P1", name="Patient 1",
                          weekly_specialty_needs={"Occupational Therapist": 2},
                          availability=availability)
        therapist = Therapist(id="T3", name="Dr. Charlie", specialty="Occupational Therapist",
                              availability=availability)
        timeslots = [
            {"id": "1", "day_of_week": "Monday", "start_time": 9.0, "end_time": 9.5},
            {"id": "2", "day_of_week": "Monday", "start_time": 9.5, "end_time": 10.0},
            {"id": "3", "day_of_week": "Monday", "start_time": 10.0, "end_time": 10.5},
            {"id": "4", "day_of_week": "Monday", "start_time": 10.5, "end_time": 11.0}
        ]
        schedule = create_schedule([patient], [therapist], timeslots)
        self.assertIsNotNone(schedule, "A schedule should be found for feasible inputs.")
        self.assertEqual(len(schedule), 4,
                         "A patient needing 2 hours should have exactly 4 half-hour sessions scheduled.")

    def test_create_complex_test_case_structure(self):
        """
        Test that the create_complex_test_case function returns a tuple containing:
         - a list of patients,
         - a list of therapists, and
         - a list of timeslots with the correct structure.
        """
        patients, therapists, timeslots = create_complex_test_case()
        self.assertIsInstance(patients, list)
        self.assertIsInstance(therapists, list)
        self.assertIsInstance(timeslots, list)
        # Verify that each patient and therapist has availability for weekdays (subset of WeekDay)
        expected_days = {day.value for day in WeekDay}
        for patient in patients:
            self.assertTrue(set(patient.availability.keys()).issubset(expected_days))
        for therapist in therapists:
            self.assertTrue(set(therapist.availability.keys()).issubset(expected_days))
        # Verify timeslot structure
        for ts in timeslots:
            self.assertIn("id", ts)
            self.assertIn("day_of_week", ts)
            self.assertIn("start_time", ts)
            self.assertIn("end_time", ts)

if __name__ == "__main__":
    unittest.main()
