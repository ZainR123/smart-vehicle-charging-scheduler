"""Informal testing attempts for the Cumulative FCFS scheduler. Unit tests are preferrable."""

import unittest
from scheduler.scheduling import TimeSlot, Vehicle, Scheduler
from scheduler.cumulative_fcfs_scheduler import CumulativeFCFSScheduler


class CumulativeFCFSSchedulerTest(unittest.TestCase):
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

    def test_is_valid_vehicle(self):
        output = CumulativeFCFSScheduler(Scheduler)._is_valid_vehicle(None)
        self.assertFalse(output)

    def test_is_valid_vehicle2(self):
        output = CumulativeFCFSScheduler(Scheduler)._is_valid_vehicle(Vehicle(0, 720, 10, 30, 0))
        self.assertTrue(output)

    def test_get_timeslot_index(self):
        output = CumulativeFCFSScheduler(Scheduler)._get_timeslot_index(25)
        self.assertEqual(2, output)

    def test_get_timeslot_index2(self):
        output = CumulativeFCFSScheduler(Scheduler)._get_timeslot_index(-5)
        self.assertEqual(0, output)

    def test_is_valid_timeslot(self):
        invalid_timeslot_1 = TimeSlot(-5, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                      self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        output = CumulativeFCFSScheduler(Scheduler)._is_valid_timeslot(invalid_timeslot_1)
        self.assertFalse(output)

    def test_is_valid_timeslot2(self):
        invalid_timeslot_1 = TimeSlot(5, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                      self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        output = CumulativeFCFSScheduler(Scheduler)._is_valid_timeslot(invalid_timeslot_1)
        self.assertTrue(output)

    def test_has_all_inputs(self):
        output = CumulativeFCFSScheduler(Scheduler)._has_all_inputs(None, None)
        self.assertFalse(output)

    def test_has_all_inputs2(self):
        valid_timeslot_1 = TimeSlot(5, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                    self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        valid_timeslot_2 = TimeSlot(10, self.DUMMY_RENEWABLE, self.DUMMY_MAX_CAPACITY,
                                    self.DUMMY_PREDICTED_LOAD, self.DUMMY_HIGHEST_LOAD)
        timeslots = [valid_timeslot_1, valid_timeslot_2]
        output = CumulativeFCFSScheduler(Scheduler)._has_all_inputs(Vehicle(0, 720, 10, 30, 0), timeslots)
        self.assertEquals(None, output)

    def test_has_all_inputs3(self):
        output = CumulativeFCFSScheduler(Scheduler)._has_all_inputs(None, timeslots=[])
        self.assertFalse(output)

    def test_is_within_wait_time(self):
        output = CumulativeFCFSScheduler(Scheduler)._is_within_wait_time(5, Vehicle(0, 720, 10, 30, 0))
        self.assertTrue(output)

    def test_is_within_wait_time2(self):
        output = CumulativeFCFSScheduler(Scheduler)._is_within_wait_time(80, Vehicle(0, 720, 10, 30, 0))
        self.assertFalse(output)

    def test__init__(self):
        output = CumulativeFCFSScheduler(Scheduler).__init__([], None)
        self.assertFalse(output)

    def test__init__2(self):
        output = CumulativeFCFSScheduler(Scheduler).__init__(None, None)
        self.assertFalse(output)

    def test__init__3(self):
        output = CumulativeFCFSScheduler(Scheduler).__init__([], [])
        self.assertFalse(output)

    def test_schedule(self):
        scheduler = CumulativeFCFSScheduler([], [])
        output = scheduler.schedule(None, [])
        self.assertEqual([], output)

    def test_schedule2(self):
        scheduler = CumulativeFCFSScheduler([], [])
        output = scheduler.schedule(None, [1])
        self.assertEqual([], output)


if __name__ == '__main__':
    unittest.main()
