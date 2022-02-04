"""DEPRECATED. This scheduler has been replaced by the more powerful LP Scheduler.
"""

from scheduler.scheduling import DynamicQueue, Scheduler
from copy import deepcopy


class CumulativeFCFSScheduler(Scheduler):
    """Naive 'cumulative' scheduler implementation that schedules using first come first serve. The earlier the
    electric vehicles schedule, the more likely they are able to obtain suitable times to schedule.

    During initialisation, the current timetable and the list structure containing the ChargingPoint objects (and
    subsequently the data on the charging points) are passed to this Scheduler object.


    Attributes:
        timetable: A 2D list representing the current timetable containing the schedules.
        charge_points: The list of charging points in the area.
    """
    MAX_TIMESLOTS_NUM = 96
    TIME_INTERVAL = 15

    def __init__(self, timetable=None, charge_points=None):
        self.timeslots = []
        self.charge_points = charge_points
        if not timetable:
            self.timetable = [[] for timeslot in range(self.MAX_TIMESLOTS_NUM)]

    def schedule(self, vehicle=None, timeslots=None):
        """Takes a vehicle as well as the data for each time slot in the day to schedule it according to the
        data for each time slot and the vehicle's needs.


        Args:
            vehicle: The Vehicle object to be scheduled.
            timeslots: The list of TimeSlot objects that each wraps the required data of each time interval
            for scheduling.

        Returns:
            A 2D list representing the updated timetable. The list is empty if either of the arguments is invalid.
        """
        self.timeslots = timeslots
        prev_timetable = deepcopy(self.timetable)
        timetable = list()

        if self._has_all_inputs(vehicle, timeslots):
            self._choose_timeslots(vehicle, self._get_required_num_of_timeslots(vehicle))
            timetable = self.timetable
            if not self.timetable:
                self.timetable = prev_timetable

        return timetable

    def _has_all_inputs(self, vehicle, timeslots):
        """Validates the input vehicle, the time slots given from the schedule method, and the timetable and the
        charging points given when constructing the Scheduler.

        Args:
            vehicle: Vehicle object given when calling the schedule method.
            timeslots: List of TimeSlot objects given when calling the schedule method.

        Returns:
            A boolean that signifies if the scheduling can (or should) proceed.
        """
        return self._is_valid_vehicle(vehicle) \
               and all(map(self._is_valid_timeslot, timeslots)) \
               and self.charge_points \
               and self.timetable

    def _get_timeslot_index(self, time):
        """Gets the index in the timetable of a given time (in minutes).

        Args:
            time: Integer representing the time (in minutes)

        Returns:
            The index that represents the given time's position in the timetable.
        """
        return round(time / self.TIME_INTERVAL)

    def _is_valid_vehicle(self, vehicle):
        """Checks if the given vehicle input is valid by checking if it is None and calling its own validation
        method.

        Args:
             vehicle: Vehicle object to validate.

        Returns:
            A boolean that signifies if the vehicle input is valid.
        """
        if vehicle is None or not vehicle.is_valid_vehicle():
            return False

        return True

    def _is_valid_timeslot(self, timeslot):
        """Checks if the given vehicle input is valid by checking if it is None and calling its own validation
        method.

        Args:
            timeslot: Vehicle object to validate.

        Returns:
            A boolean that signifies if the timeslot input in the list of time slots is valid.
        """
        if timeslot is None or not timeslot.is_valid_timeslot():
            return False

        return True

    def _has_free_charge_point(self, curr_timeslot, vehicle=None):
        """Checks if the given time slot has a free charge point/slot.
        Used as a constraints function when obtaining possible time slots.

        Args:
            curr_timeslot: The time slot to check.
            vehicle: The vehicle being scheduled. NOTE: Currently not utilised, but as all constraints functions must
            have it, this method can take in this parameter.

        Returns:
            A boolean that signifies if there is a free charging point/slot during the given time slot.
        """
        return len(self.timetable[curr_timeslot]) < len(self.charge_points)

    def _calculate_load_sum(self, curr_timeslot):
        """Calculates the current load within the given time slot.

        Args:
            curr_timeslot: The time slot where the grid load sum is calculated from.

        Returns:
            The current load during the given time slot.
        """
        load_sum = 0
        if len(self.timetable[curr_timeslot]) > 0:
            for i in range(len(self.timetable[curr_timeslot])):
                load_sum += self.charge_points[i].charge_rate
        load_sum += self.timeslots[curr_timeslot].predicted_load

        return load_sum

    def _does_not_exceed_load(self, curr_timeslot, vehicle=None):
        """Checks if scheduling a vehicle in the given time slot will cause the grid load during that time slot to
        reach or exceed the maximum grid capacity.

        Args:
            curr_timeslot: The time slot to check.
            vehicle: The vehicle being scheduled. NOTE: Currently not utilised, but as all constraints functions must
            have it, this method can take in this parameter.

        Returns:
            A boolean that signifies if scheduling a vehicle during the given time slot will cause the total load
            during that time slot to reach or exceed the maximum grid capacity.
        """
        if self._has_free_charge_point(curr_timeslot, vehicle):
            charge_point_index = len(self.timetable[curr_timeslot])
        else:
            charge_point_index = len(self.timetable[curr_timeslot]) - 1
        added_load = self.charge_points[charge_point_index].charge_rate

        return self._calculate_load_sum(curr_timeslot) + added_load < self.timeslots[curr_timeslot].max_capacity

    def _is_within_wait_time(self, curr_timeslot, vehicle):
        """Checks if the time slot is within the vehicle's acceptable wait time before starting to charge.

        Args:
            curr_timeslot: Integer that represents the time slot to be checked.
            vehicle: The vehicle object representing the vehicle that is being scheduled.

        Returns:
            A boolean that signifies if the given time slot exceeds the vehicle's acceptable wait time.
        """
        return curr_timeslot * 15 <= vehicle.arrival + vehicle.wait_time

    def _get_possible_timeslots(self, curr_timeslot, vehicle, constraint_func):
        """Returns the possible timeslots that satisfy the given constraint(s).

        Args:
            curr_timeslot: The current timeslot considered (initially, this would be the arrival time of the
            vehicle).
            vehicle: The vehicle to be scheduled.
            constraint_func: The function used to determine if a timeslot meets the given constraint(s).
            THIS MUST BE A FUNCTION THAT RETURNS A BOOLEAN.

        Returns:
            A list containing the possible timeslots the vehicle can be scheduled in,
            arranged in no particular order.
        """
        possible_timeslots = []
        for timeslot in range(curr_timeslot, self.MAX_TIMESLOTS_NUM):
            if constraint_func(timeslot, vehicle):
                possible_timeslots.append(timeslot)

        return possible_timeslots

    def _has_possible_adjacent_lists(self, timeslots, required_num_timeslots):
        """Checks if the given list of time slots has at least one sublist that has enough adjacent time slots to
        schedule the vehicle in. This informs the scheduler about a list of time slots that has gaps in it.

        Args:
            timeslots: The list of time slots to check.
            required_num_timeslots: Number of time slots required to satisfy whole charge duration.

        Returns:
            A boolean tha signifies if an appropriate sequence of time slots that can be used
            to choose adjacent time slots from exists in the given list.
        """
        enough_adjacent_timeslots = False

        if len(timeslots) == 1 and required_num_timeslots == 1:  # no need to check if there is only one time slot
            return True

        for i in range(1, len(timeslots)):
            count = 0
            for j in range(i, len(timeslots)):
                if timeslots[j] - timeslots[j-1] > 1:
                    break
                count += 1

            if count >= required_num_timeslots:
                enough_adjacent_timeslots = True
                break
            else:
                break

        return enough_adjacent_timeslots

    def _get_optimal_timeslots(self, vehicle, required_num_timeslots):
        """Gets the optimal time slots that the vehicle can be scheduled in.

        Args:
            vehicle: The Vehicle object being scheduled
            required_num_timeslots: Number of time slots required to satisfy whole charge duration.

        Returns:
            The list of analysed time slots that the scheduler can choose to schedule the vehicle.
        """
        # Start considering time slots from the time of the vehicle's arrival
        curr_timeslot = self._get_timeslot_index(vehicle.arrival)

        # Get lists of time slots, with each list satisfying the main criteria
        timeslots_by_availability = self._get_possible_timeslots(curr_timeslot, vehicle, self._has_free_charge_point)
        timeslots_by_load = self._get_possible_timeslots(curr_timeslot, vehicle, self._does_not_exceed_load)
        possible_timeslots = \
            set(timeslots_by_availability).intersection(timeslots_by_load)

        # If there are common time slots between the the two lists and these can all be used to schedule for the
        # whole charge duration and there are enough adjacent time slots to do so, then use the intersection of the
        # two lists.
        # Else if this is not the case, then check the list with the time slots that do not exceed the load for the same
        # things.
        # If none of the two above are the case, then simply schedule from the available time slots.
        if possible_timeslots \
                and len(possible_timeslots) >= required_num_timeslots \
                and self._has_possible_adjacent_lists(list(possible_timeslots), required_num_timeslots):
            optimal_timeslots = self._get_adjacent_timeslots_by_min_priority(
                list(possible_timeslots), vehicle)
        elif timeslots_by_load \
                and len(timeslots_by_load) >= required_num_timeslots\
                and self._has_possible_adjacent_lists(timeslots_by_load, required_num_timeslots):
            optimal_timeslots = self._get_adjacent_timeslots_by_min_priority(
                list(set(timeslots_by_load).intersection(timeslots_by_availability)), vehicle)
        else:
            optimal_timeslots = self._get_adjacent_timeslots_by_min_priority(timeslots_by_availability, vehicle)

        return optimal_timeslots

    def _get_required_num_of_timeslots(self, vehicle):
        """Gets the required number of time slots to fully schedule the vehicle.

        Args:
            vehicle: The vehicle object to be scheduled.

        Returns:
            Integer representing the number of time slots needed to schedule the vehicle for the whole charge duration.
        """
        duration = vehicle.duration
        timeslots_num = 0
        while duration > 0:
            timeslots_num += 1
            duration -= 15

        return timeslots_num

    def _get_adjacent_timeslots_by_min_priority(self, timeslots, vehicle):
        """Method returns n adjacent time slots from the possible time slots.
        
        NOTE: PROTOTYPE IMPLEMENTATION. Code is unfortunately quite messy so it would be helpful to clean it up if
        time permits.
        
        Args:
            timeslots: A list of TimeSlot objects where the adjacent time slots are taken from.
            vehicle: The Vehicle object that represents the vehicle being scheduled.

        Returns:
            A DynamicQueue of TimeSlots containing the adjacent TimeSlots, with the front part containing time
            slots with the earliest time values.
        """
        timeslots_num = self._get_required_num_of_timeslots(vehicle)

        curr_min = float("inf")
        curr_timeslot_index = 0

        for i in range(len(timeslots) - timeslots_num):
            # Then consider n time slots where n is timeslots_num. Do not consider set of time slots if there is a gap
            # between them as the list creation in _get_optimal_timeslot does not consider this...
            curr_sum = 0
            has_gap = False
            j = i + timeslots_num - 1
            while j > 0:
                if timeslots[j] - timeslots[j-1] > 1:
                    has_gap = True
                    break
                curr_sum += self.timeslots[timeslots[i+j]].priority
                j -= 1
                
            if curr_sum < curr_min and not has_gap:
                curr_min = curr_sum
                curr_timeslot_index = i

            # If the next n sequence of time slots isn't within the wait time, stop searching more sequences
            if not self._is_within_wait_time(timeslots[i + timeslots_num], vehicle):
                break

        return DynamicQueue(timeslots[curr_timeslot_index:])

    def _choose_timeslots(self, vehicle, required_num_timeslots):
        """Called by the main schedule method to choose the time slots to schedule the vehicle in.

        Args:
            vehicle: Vehicle object to be scheduled.
            required_num_timeslots: Number of time slots required to satisfy whole charge duration.

        Returns:
            A list of time slots representing the scheduled times for the vehicle. If the list is empty, then the
            scheduler failed to find enough suitable time slots to schedule the vehicle in.
        """
        chosen_timeslots = self._get_optimal_timeslots(vehicle, required_num_timeslots)

        if len(chosen_timeslots) < required_num_timeslots:
            self.timetable = []
        else:
            count = 0
            while count < required_num_timeslots:
                timeslot = chosen_timeslots.dequeue()
                self.timetable[timeslot].append(vehicle)
                count += 1
