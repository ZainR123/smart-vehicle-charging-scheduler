import unittest

from scheduler.scheduling import TimeSlot, Vehicle
from generators.renewable_generator import RenewableGenerator
from generators.grid_load_generator import GridLoadGenerator


class SchedulingSetupTest(unittest.TestCase):
    DUMMY_TIME = 45
    DUMMY_RENEWABLE = 0.64
    DUMMY_MAX_CAPACITY = 78.14
    DUMMY_PREDICTED_LOAD = 51.24
    DUMMY_HIGHEST_LOAD = 42.0
    DUMMY_ID = 0
    DUMMY_ARRIVAL = 5
    DUMMY_DURATION = 35
    DUMMY_WAIT = 30
    DUMMY_CHARGE = 48

    def test_rejects_invalid_timeslot_time(self):
        invalid_timeslot_1 = TimeSlot(-5, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                    self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        invalid_timeslot_2 = TimeSlot(1441, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                    self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)

        self.assertFalse(invalid_timeslot_1.is_valid_timeslot() and invalid_timeslot_2.is_valid_timeslot())

    def test_rejects_valid_timeslot_time(self):
        valid_timeslot_1 = TimeSlot(0, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                    self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        valid_timeslot_2 = TimeSlot(96, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                    self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)

        self.assertTrue(valid_timeslot_1.is_valid_timeslot() and valid_timeslot_2.is_valid_timeslot())

    def test_priority_calculated_correctly(self):
        expected_priority = round(self.DUMMY_PREDICTED_LOAD / self.DUMMY_HIGHEST_LOAD + 1 - self.DUMMY_RENEWABLE, 1)
        timeslot = TimeSlot(self.DUMMY_TIME, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                            self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        self.assertEqual(expected_priority, timeslot.calculate_priority())

    def test_rejects_invalid_vehicle_arrival_time(self):
        invalid_vehicle_1 = Vehicle(self.DUMMY_ID, -35, self.DUMMY_DURATION, self.DUMMY_WAIT, self.DUMMY_CHARGE)
        invalid_vehicle_2 = Vehicle(self.DUMMY_ID, 1441, self.DUMMY_DURATION, self.DUMMY_WAIT, self.DUMMY_CHARGE)
        invalid_vehicle_3 = Vehicle(self.DUMMY_ID, 31.5, self.DUMMY_DURATION, self.DUMMY_WAIT, self.DUMMY_CHARGE)
        invalid_vehicle_4 = Vehicle(1.5, self.DUMMY_TIME, self.DUMMY_DURATION, self.DUMMY_WAIT,
                                    self.DUMMY_CHARGE)
        invalid_vehicle_5 = Vehicle(-6, self.DUMMY_TIME, self.DUMMY_DURATION, self.DUMMY_WAIT, self.DUMMY_CHARGE)
        invalid_vehicle_list = [invalid_vehicle_1, invalid_vehicle_2, invalid_vehicle_3,
                                invalid_vehicle_4, invalid_vehicle_5]

        self.assertFalse(any([ev.is_valid_vehicle() for ev in invalid_vehicle_list]))

    def test_grid_load_generator_generates_96_values(self):
        load_gen = GridLoadGenerator()
        self.assertEqual(96, len(load_gen.generated_data))

    def test_renewable_generator_generates_96_values(self):
        renewable_gen = RenewableGenerator()
        self.assertEqual(96, len(renewable_gen.generated_data))


if __name__ == '__main__':
    unittest.main()
