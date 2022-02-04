"""DEPRECATED. This module was used for the Cumulative FCFS Scheduler which has now been replaced by the more
powerful LP Scheduler.
"""

from collections import deque
from abc import abstractmethod


class Scheduler:
    """Base abstract class for different types of schedulers."""

    @abstractmethod
    def schedule(self, vehicle, timeslots):
        pass


class TimeSlot:
    """TimeSlot class to wrap data/state of each time slot.

    Attributes:
        time: The time in minutes of the current timeslot.

        renewable_perc: The predicted percentage data of renewables (i.e. solar and wind) generated during this
        time slot.

        max_capacity: The maximum capacity of the grid during this time slot. The amount of
        energy used during the current time slot must not exceed this value.

        predicted_load: The predicted load during this time slot. This is used
        within the calculation of priority value.

        highest_load: The highest predicted load for the set of time slots this time slot
        belongs to--i.e. the highest predicted load for the day.

        priority: The priority value of the current time slot. Currently, with
        the simple priority formula, the lower values have higher priority.
    """
    def __init__(self, time, renewable_perc, max_capacity, predicted_load, highest_load):
        self.time = time
        self.renewable_perc = renewable_perc
        self.max_capacity = max_capacity
        self.predicted_load = predicted_load
        self.highest_load = highest_load
        self.priority = self.calculate_priority()

    def _calculate_non_renewable_mix_perc(self):
        """This calculates the sum of the percentages of non-renewables.

        NOTE: FOR INITIAL DEVELOPMENT AND TESTING, THERE IS THE ASSUMPTION THAT
        "NON-RENEWABLES" HERE REFER TO ANYTHING THAT IS NOT SOLAR AND WIND.

        Returns:
            Percentage of non-renewable sources generated during
            this time slot.
        """
        return 1 - self.renewable_perc

    def calculate_priority(self):
        """This calculates the priority value for this time slot

        Returns:
            The priority value for this time slot. Currently, this value is
            such that the lower it is, the higher its priority.
        """
        return round(self.predicted_load / self.highest_load + self._calculate_non_renewable_mix_perc(), 1)

    def is_valid_timeslot(self):
        """Validates the time slot.

        Returns:
             A boolean representing the validity of the data assigned to the time slot.
        """
        if any([val is None for val in (self.time, self.renewable_perc, self.max_capacity,
                                        self.predicted_load, self.highest_load, self.priority)
                ]) \
                or not (0 <= self.time <= 1440) \
                or self.highest_load > self.max_capacity:
            return False

        return True

    def __lt__(self, other):
        return self.priority < other.priority

    def __gt__(self, other):
        return self.priority > other.priority

    def __str__(self):
        return "Time: " + str(self.time) \
               + "\nPriority: " + str(self.priority) \
               + "\nPredicted load: " + str(self.predicted_load) \
               + "\nHighest load: " + str(self.highest_load)


class Vehicle:
    """Vehicle class that wraps all information about the vehicle.

    Attributes:
        ev_id: ID of the vehicle.
        arrival: The time the vehicle arrives in the simulation area.
        duration: The duration of charge to meet the vehicle's charging demands.
        wait_time: The acceptable time after arrival that the vehicle wants to schedule by.
        charge: The vehicle's state of charge just before charging.
        capacity: The vehicle's battery capacity.
        time_pref: The preferred time to charge.
    """
    def __init__(self, ev_id, arrival, duration, wait_time, charge, capacity, time_pref):
        self.id = ev_id
        self.arrival = arrival
        self.duration = duration
        self.wait_time = wait_time
        self.charge = charge
        self.capacity = capacity
        self.time_pref = time_pref

    def is_valid_vehicle(self):
        """Validates the vehicle.

        Returns:
             A boolean representing the validity of the data assigned to the Vehicle.
        """
        if any([val is None for val in (self.id, self.arrival, self.duration, self.wait_time)])\
                or not (0 <= self.arrival <= 1440)\
                or self.id < 0\
                or any([x % 1 != 0 for x in (self.id, self.arrival) if x != 0]):
            return False

        return True

    def __str__(self):
        return "ID: " + str(self.id) \
               + "\nArrival time: " + str(self.arrival) \
               + "\nCharge duration: " + str(self.duration) \
               + "\nAcceptable wait time: " + str(self.wait_time) \
               + "\nCurrent state of charge: " + str(self.charge)


class ChargingPoint:
    """Represents a charging point.

    NOTE: THIS CLASS WAS CREATED IN CASE MORE DATA NEEDS TO BE WRAPPED AROUND EACH OF THE CHARGING POINTS.

    Attributes:
        charge_rate: The charge rate of the charging point.
    """
    STATIC_CHARGE_RATE = 22

    def __init__(self):
        self.charge_rate = ChargingPoint.STATIC_CHARGE_RATE


class DynamicQueue:
    """Dynamic queue implementation that wraps a collections.deque object.
    Provides basic functionality for a dynamic queue.

    Attributes:
        _queue: The internal deque object.
    """
    def __init__(self, l=iter([])):
        self._queue = deque(l)

    def enqueue(self, item):
        self._queue.append(item)

    def enqueue_front(self, item):
        self._queue.appendleft(item)

    def peek(self):
        return self._queue[0]

    def dequeue(self):
        try:
            return self._queue.popleft()
        except IndexError:
            return None

    def is_empty(self):
        return True if len(self) == 0 else False

    def __len__(self):
        return len(self._queue)

    def __str__(self):
        return str(self._queue)

    def __iter__(self):
        return iter(self._queue)
