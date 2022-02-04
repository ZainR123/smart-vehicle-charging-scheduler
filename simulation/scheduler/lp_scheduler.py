"""DOcplex Mathematical Programming Reference Manual
http://ibmdecisionoptimization.github.io/docplex-doc/mp/py-modindex.html
"""
import math

from docplex.mp.model import Model
from abc import abstractmethod
from datetime import timedelta, datetime
from copy import deepcopy

# Constants
MINS_IN_DAY = 1440
MINS_IN_HOUR = 60


class ScheduleInfo:
    """Wrapper object to collect information for a single vehicle schedule within a single
    time slot/interval. Multiple ScheduleInfo objects should exist in a single time interval within the timetable
    if there are multiple vehicles scheduled in that time interval.

    Attributes:
        ev_id: The id of the electric vehicle scheduled in the time interval.
        charge: The amount of electricity put into the electric vehicle in the time interval.
        charger_id: The id of the charger that the electric vehicle is scheduled into.
        arrival: The vehicle's scheduled time of arrival in a datetime format.
        departure: The vehicle's scheduled time of departure in a datetime format.
    """
    def __init__(self, ev_id, charge, charger_id, arrival, departure):
        self.ev_id = ev_id
        self.charge = charge
        self.charger_id = charger_id
        self.arrival = arrival
        self.departure = departure

    def is_valid(self):
        """Checks if the wrapped values for a vehicle's time interval schedule are valid.

        Returns:
            True if all data items are valid, false if otherwise.
        """
        if self.ev_id < 0 or self.charger_id < 0 \
                or self.arrival < 0 or self.arrival > MINS_IN_DAY \
                or self.departure < 0 or self.departure > MINS_IN_DAY:
            return False

        return True


class TimeSlotInfo:
    """Wrapper object to collect information for a single time interval.

    Attributes:
        date_time: The datetime object representing the time interval's time and date information
        traditional_prod: The total traditional electricity production in the time interval.
        consumption: The total electricity consumption in the time interval.
        renewables_prod: The total production of renewable production in the time interval.
        max_capacity: The maximum load capacity of the grid during this time interval.
        existing_schedules: A list of ScheduleInfo objects representing the individual vehicle-time interval
                            schedules that are already present in this time interval (i.e., if there are two vehicles
                            scheduled in time interval, there will be two ScheduleInfo objects).
    """
    def __init__(self, date_time, traditional_prod, consumption, renewables_prod, max_capacity,
                 available_chargers, existing_schedules=None, price_tariff=None):
        self.date_time = date_time
        self.traditional_prod = traditional_prod
        self.renewables_prod = renewables_prod
        self.consumption = consumption
        self.max_capacity = max_capacity
        self.available_chargers = deepcopy(available_chargers)
        self.existing_schedules = [] if not existing_schedules else existing_schedules
        self.price_tariff = 0 if not price_tariff else price_tariff

    def is_valid(self):
        """Checks if the wrapped data values for the time slot are valid.

        Returns:
            True if all data items are valid, false if otherwise.
        """
        if not isinstance(self.date_time, datetime)\
                or any(n < 0 for n in [self.traditional_prod, self.renewables_prod,
                                       self.consumption, self.max_capacity,
                                       self.price_tariff]):
            return False

        return True


class VehicleInfo:
    """Wrapper object to collect information for a single electric vehicle to be scheduled.

    Attributes:
        ev_id: The id of the electric vehicle to be scheduled.
        time_period: The time period from the time of arrival to the time of departure, in the format
                     (arrival_datetime, departure_datetime)
        arrival_soc: The electric vehicle's state of charge at arrival.
        soc_demand: The state of charge to aim for after charging.
        battery_capacity: The battery capacity of the electric vehicle (in kWh).
        charger_id: The charger the vehicle will use to charge.
    """
    def __init__(self, ev_id, time_period, arrival_soc, soc_demand, battery_capacity, charger_id):
        self.id = ev_id
        self.time_period = time_period
        self.arrival_soc = arrival_soc
        self.soc_demand = soc_demand
        self.battery_capacity = battery_capacity
        self.charger_id = charger_id

    def is_valid(self):
        """Checks if the wrapped data values for the vehicle are valid.

        Returns:
            True if all data items are valid, false if otherwise.
        """
        if self.id < 0 \
                or not (0 <= self.arrival_soc <= 100) \
                or any(map(lambda dt: not isinstance(dt, datetime), self.time_period))\
                or self.battery_capacity < 0\
                or self.charger_id < 0:
            return False

        return True


class Timetable:
    """Wrapper object containing schedule information within a time period.

    Attributes:
        timetable: A list of lists of ScheduleInfo wrapper objects, representing schedule information for a single
                   vehicle within a time slot/interval.
    """
    SCHEDULED_SUCCESSFULLY = 0
    CHARGER_CONFLICT = 1
    SCHEDULE_INFEASIBLE = 2

    def __init__(self, timetable, timetable_start, schedule_status):
        self.timetable = timetable
        self.timetable_start = timetable_start
        self.schedules = None
        self.schedule_status = schedule_status

    def get_schedules(self):
        """Returns a compact representation of the schedule in the timetable.

        Returns:
            A dictionary representation of the scheduled charging times in the format:
            {ev_id: {'arrival': arrival_datetime, 'departure': departure_datetime, 'charge': total_schedule_charge}}
        """
        if not self.schedules:
            ev_schedules = dict()

            # Go through the timetable, for each time a new vehicle is encountered, add it and its arrival to the
            # dictionary. If it's already in the dictionary, update the departure.
            for ts in self.timetable:
                for s in ts:
                    if s.ev_id not in ev_schedules:
                        ev_schedules[s.ev_id] = dict()
                        ev_schedules[s.ev_id]["arrival"] = s.arrival
                        ev_schedules[s.ev_id]["charge"] = 0
                    ev_schedules[s.ev_id]["departure"] = s.departure
                    ev_schedules[s.ev_id]["charge"] += s.charge

            self.schedules = ev_schedules

        return self.schedules

    def get_schedule_status(self):
        """Returns a compact representation of the status of each scheduling attempt.

        Returns:
            A dictionary representation of the scheduling status for each vehicle.
        """
        return self.schedule_status


class LPScheduler:
    """Advance scheduler implementation that models the problem as a mathematical mixed-integer linear programming
    problem (MILP) and solves it using CPLEX.

    Producers and consumers must be given in a list format where the index is their ID.

    Attributes:
        _allocator: Strategy for allocating the initial time of charging for each vehicle. This is set to First Choice
                    Allocation by default if no strategy is supplied.
        _optimiser: The MILP optimiser to compute and solve the charging decisions for each time slot.
        interval_length: The length of each time interval or time slot (in minutes). This is set to 15 minutes by
                         default.
        producers: The list of electricity producers involved in the simulated environment.
        consumers: The list of electricity consumers involved in the simulated environment.
        renewables_producers: The list of electricity generators from renewable sources that are involved in
                              the simulation env.
        charger_rates: The list of charging rates for each charger where the index is the charger ID.
    """
    def __init__(self, producers, consumers, renewables_producers, charger_rates,
                 interval_length=15, allocation_strategy=None):
        self._optimiser = LPTimeSlotOptimiser()
        self.producers = producers
        self.consumers = consumers
        self.renewables_producers = renewables_producers
        self.charger_rates = charger_rates
        self.interval_length = interval_length
        self._allocator = allocation_strategy if allocation_strategy else FirstChoiceAllocation()

    def schedule(self, vehicles, timeslots):
        """Schedules all provided vehicles within the time period specified by the time slots.

        Args:
            vehicles: A list of VehicleInfo objects representing all scheduling information related to the vehicle.
            timeslots: A list of TimeSlotInfo objects representing all scheduling information related to the vehicle.
                       IMPORTANT: THE TIMES MUST BE DISCRETISED INTO THE SPECIFIED INTERVAL LENGTH.

        Returns:
            A Timetable representing the charging schedule of all the given vehicles.
        """
        if not self.all_inputs_valid(vehicles, timeslots):
            return None
        first_interval, last_interval = self._get_first_and_last_interval(timeslots)

        # Order does not matter for both TimeSlotInfo objects (time intervals are sorted) and VehicleInfo objects (no
        # ordering requirement). Each vehicle is assigned a 'local id' to be used solely within scheduling.
        sorted_timeslots = self._sort_timeslots(timeslots)

        unpacked_ts_info = self._convert_timeslots_info_to_lists(sorted_timeslots)
        unpacked_ev_info = self._convert_vehicles_info_to_lists(vehicles, first_interval)
        ts_allocations = self._allocator.allocate(unpacked_ev_info, unpacked_ts_info, self.interval_length)
        charge_rates = [self.charger_rates[charger_id] for charger_id in unpacked_ev_info["charger_ids"]]

        # Vehicles already scheduled must have local IDs that come after the local ids of vehicles to be scheduled
        scheduled_vehicles = self._get_existing_charges_as_vehicles(sorted_timeslots, first_interval)
        scheduled_unpacked_ev_info = self._convert_vehicles_info_to_lists([scheduled_vehicles[ev_id]
                                                                           for ev_id in
                                                                           scheduled_vehicles.keys()],
                                                                          first_interval)
        # Allocate time slots to already scheduled vehicles using first choice strategy
        scheduled_vehicles_ts_allocations = FirstChoiceAllocation().allocate(scheduled_unpacked_ev_info,
                                                                             unpacked_ts_info,
                                                                             self.interval_length)
        existing_scheduled_evs = {"unpacked_ev_info": scheduled_unpacked_ev_info,
                                  "ts_allocations": scheduled_vehicles_ts_allocations}

        charge_matrix, scheduled_ev_charge_matrix = self._optimiser.optimise(unpacked_ev_info,
                                                                             unpacked_ts_info,
                                                                             charge_rates,
                                                                             ts_allocations,
                                                                             self.interval_length,
                                                                             existing_scheduled_evs=existing_scheduled_evs)
        new_time_period_schedule = self._create_new_time_period_schedule(charge_matrix,
                                                                         first_interval,
                                                                         last_interval)
        charge_schedule = self._create_timetable(charge_matrix,
                                                 ts_allocations,
                                                 new_time_period_schedule,
                                                 first_interval,
                                                 vehicles,
                                                 scheduled_vehicles_ts_allocations,
                                                 scheduled_ev_charge_matrix,
                                                 scheduled_unpacked_ev_info,
                                                 scheduled_vehicles)

        return charge_schedule

    def all_inputs_valid(self, vehicles, timeslots):
        """Simple validation for validity of individual data items in the list of VehicleInfo and TimeSlotInfo
        objects

        Args:
            vehicles: A list of VehicleInfo objects to be validated.
            timeslots: A list of TimeSlotInfo objects to be validated.

        Returns:
            True if all data items are valid, false otherwise.
        """
        for ev in vehicles:
            if not ev.is_valid():
                return False
        for ts in timeslots:
            if not ts.is_valid():
                return False

        return True


    def _convert_timeslots_info_to_lists(self, timeslots):
        """Converts the TimeSlotInfo objects' wrapped values into individual lists wrapped inside a dictionary.

        Args:
            timeslots: A list of TimeSlotInfo objects.

        Returns:
            A dictionary of lists representing each list of time interval data.
        """
        traditional_prod = []
        consumption = []
        renewables_prod = []
        max_capacity = []
        available_chargers = []
        interval_start_times = []
        interval_end_times = []
        price_tariffs = []

        scheduling_window_start = timeslots[0].date_time.replace(hour=0, minute=0, second=0)  # Remove h/m/s
        for ts in timeslots:
            traditional_prod.append(ts.traditional_prod)
            consumption.append(ts.consumption)
            renewables_prod.append(ts.renewables_prod)
            max_capacity.append(ts.max_capacity)
            available_chargers.append(ts.available_chargers)
            price_tariffs.append(ts.price_tariff)
            interval_start_times.append(self.convert_datetime_to_minutes_with_offset(ts.date_time,
                                                                                     scheduling_window_start))
            interval_end_times.append(self.convert_datetime_to_minutes_with_offset(ts.date_time,
                                                                                   scheduling_window_start)
                                      + 15)

        return {"traditional_prod": traditional_prod,
                "consumption": consumption,
                "renewables_prod": renewables_prod,
                "max_capacity": max_capacity,
                "available_chargers": available_chargers,
                "interval_start_times": interval_start_times,
                "interval_end_times": interval_end_times,
                "price_tariffs": price_tariffs}

    def _convert_vehicles_info_to_lists(self, vehicles, scheduling_window_start):
        """Converts information about each vehicle, such as their ID and battery capacity, into lists. This method
        effectively assigns each vehicle a local ID for use solely within the scheduler, indicated by the indices in the
        lists.

        Args:
            vehicles: List of VehicleInfo objects containing info on vehicles to be scheduled.

        Returns:
            A dictionary of lists with the following (string) keys:
                - ev_ids: A list of EV IDs where the index is the assigned local ID to be used for optimisation.
                - ev_demand: A list of kWh demands to be put into the EVs. Index is the local ID of EV.
                - arrival_times: A list of arrival times. Index is the local ID of EV.
                - departure_times: A list of departure times. Index is the local ID of EV.
                - charge_battery_limit: A list of limits for how much (kWh) can be put in. Index is the local ID of EV.
                - charger_ids: A list of charger IDs that the EVs to be scheduled will use. Index is the local ID of EV.
        """
        ev_ids = []
        arrival_times = []
        departure_times = []
        ev_demand = []
        charge_battery_limit = []
        charger_ids = []
        charger_rates = []

        for vehicle in vehicles:
            ev_ids.append(vehicle.id)
            arrival_times.append(self.convert_datetime_to_minutes_with_offset(vehicle.time_period[0],
                                                                              scheduling_window_start))
            departure_times.append(self.convert_datetime_to_minutes_with_offset(vehicle.time_period[1],
                                                                                scheduling_window_start))
            ev_demand.append(math.floor((vehicle.soc_demand - vehicle.arrival_soc) / 100
                                        * vehicle.battery_capacity))
            charge_battery_limit.append((100 - vehicle.arrival_soc) / 100
                                        * vehicle.battery_capacity)
            charger_ids.append(vehicle.charger_id)
            charger_rates.append(self.charger_rates[vehicle.charger_id])

        return {"ev_ids": ev_ids,
                "ev_demand": ev_demand,
                "arrival_times": self._discretise_times(arrival_times),
                "departure_times": self._discretise_times(departure_times),
                "charge_battery_limit": charge_battery_limit,
                "charger_ids": charger_ids,
                "charger_rates": charger_rates}

    def convert_datetime_to_minutes_with_offset(self, date_time, offset):
        """Convert datetime to minutes with the first interval of the scheduling window as the offset datetime for
        the day. Passing the same datetime results in a a value in the range [0, 1439].

        Args:
            date_time: Datetime object to convert to minutes based on the offset datetime.
            offset: Datetime object that represents the offset to be used in conversion. Represents the beginning of
                    the window, such that the offset is time 0 (or minute 0).

        Returns:
            The datetime in minutes (based on the offset).
        """
        return MINS_IN_DAY * (date_time.replace(hour=0, minute=0, second=0)
                              - offset.replace(hour=0, minute=0, second=0)).days \
               + date_time.hour * MINS_IN_HOUR \
               + date_time.minute

    def _sort_timeslots(self, timeslots):
        """Sorts time slots by their date_time attribute.

        Args:
            timeslots: A list of TimeSlotInfo objects to be sorted.

        Returns:
            A sorted list of TimeSlotInfo objects.
        """
        return sorted(timeslots, key=lambda ts: ts.date_time)

    def discretise_time(self, time):
        """Takes a time (t) in minutes and discretise them into the appropriate time interval length.
        Discretisation depends on which half the time is located in the current interval.

        If it is on the lesser half, then the time is discretised into the beginning of the interval. Otherwise,
        (if it is on the greater half) then the time is discretised into the beginning of the next interval.

        Args:
            time: Time in minutes.

        Returns:
            The discretised time in minutes.
        """
        rem = time % self.interval_length
        if rem == 0:
            return time

        if rem < round(self.interval_length / 2):
            return time - rem
        else:
            return time + self.interval_length - rem

    def _discretise_times(self, times):
        """Takes a list of times in minutes and discretise them into the appropriate time interval length.
        Discretisation depends on which half the time is located in the current interval.

        If it is on the lesser half, then the time is discretised into the beginning of the interval. Otherwise,
        (if it is on the greater half) then the time is discretised into the beginning of the next interval.

        Args:
            times: A list of times (in minutes).

        Returns:
            A list of discretised times (in minutes).
        """
        temp_times = times.copy()
        for ts_i in range(len(temp_times)):
            temp_times[ts_i] = self.discretise_time(temp_times[ts_i])

        return temp_times

    def convert_minutes_to_timedelta(self, time):
        """Converts minutes to timedelta.

        Args:
            time: Time in minutes.

        Returns:
            The timedelta representation of the discretised time.
        """
        hours = time % MINS_IN_DAY // MINS_IN_HOUR
        minutes = int((time / MINS_IN_HOUR % 1) * MINS_IN_HOUR)

        return timedelta(minutes=minutes, hours=hours)

    def _create_timetable(self, charge_matrix, ts_allocations, new_time_period_schedule, offset,
                          ev_info, scheduled_ev_ts_allocations, scheduled_ev_charge_matrix,
                          scheduled_ev_info, scheduled_evs):
        """Creates a matrix of ScheduleInfo objects that represent charge allocations.

        Args:
            charge_matrix: A matrix representing how much charge is put into each interval for each vehicle.
            new_time_period_schedule: The new schedule of each vehicle according to the first and last allocated charge.
            ev_info: A list of VehicleInfo objects representing vehicles that requested scheduling.

        Returns:
            A Timetable representing all the electric vehicle charging schedules (arrival and departure times are based
            on the first and last charge allocation of each vehicle in the charge matrix).
        """
        num_evs, num_ts, num_scheduled_evs = len(charge_matrix), len(charge_matrix[0]), len(scheduled_evs)
        schedule_status = dict()
        timetable = [[] for ts in range(num_ts)]

        for ts_i in range(num_ts):
            for ev_i in range(num_evs):
                if charge_matrix[ev_i][ts_i] > 0:
                    arrival = new_time_period_schedule[ev_i]["arrival"]
                    departure = new_time_period_schedule[ev_i]["departure"]
                    ts_schedule = ScheduleInfo(ev_info[ev_i].id,
                                               charge_matrix[ev_i][ts_i],
                                               ev_info[ev_i].charger_id,
                                               arrival,
                                               departure)
                    timetable[ts_i].append(ts_schedule)

        # Add status of vehicles that requested to schedule
        for ev_i in range(num_evs):
            if all(ev_charge_row == 0 for ev_charge_row in charge_matrix[ev_i]):
                if all(ts_allocation_row == 0 for ts_allocation_row in ts_allocations[ev_i]):
                    schedule_status[ev_i] = Timetable.CHARGER_CONFLICT
                else:
                    schedule_status[ev_i] = Timetable.SCHEDULE_INFEASIBLE
            else:
                schedule_status[ev_i] = Timetable.SCHEDULED_SUCCESSFULLY

        for ts_i in range(num_ts):  # Add existing vehicles
            for ev_i in range(len(scheduled_evs)):
                if scheduled_ev_ts_allocations[ev_i][ts_i] > 0:
                    arrival = scheduled_evs[scheduled_ev_info["ev_ids"][ev_i]].time_period[0]
                    departure = scheduled_evs[scheduled_ev_info["ev_ids"][ev_i]].time_period[1]
                    ts_schedule = ScheduleInfo(scheduled_ev_info["ev_ids"][ev_i],
                                               scheduled_ev_charge_matrix[ev_i][ts_i],
                                               scheduled_ev_info["charger_ids"][ev_i],
                                               arrival,
                                               departure)
                    timetable[ts_i].append(ts_schedule)

        return Timetable(timetable, offset, schedule_status)

    def _get_first_and_last_interval(self, ts_info):
        """Obtains the first and last interval of the scheduling window.

        Args:
            ts_info: A list of TimeSlotInfo objects representing all scheduling information related to the vehicle.

        Returns:
            A tuple T where T[0] is the first interval of the scheduling window and T[1] is the last interval of the
            scheduling window.
        """
        num_ts = len(ts_info)

        first_interval_datetime = min(ts_info[ts_i].date_time for ts_i in range(num_ts))
        first_interval_in_min = self.discretise_time(
            self.convert_datetime_to_minutes_with_offset(first_interval_datetime,first_interval_datetime)
        )
        first_interval = datetime(first_interval_datetime.year,
                                  first_interval_datetime.month,
                                  first_interval_datetime.day) \
                         + self.convert_minutes_to_timedelta(first_interval_in_min)

        last_interval_datetime = max(ts_info[ts_i].date_time for ts_i in range(num_ts))
        last_interval_in_min = self.discretise_time(
            self.convert_datetime_to_minutes_with_offset(last_interval_datetime, last_interval_datetime))
        last_interval = datetime(last_interval_datetime.year,
                                 last_interval_datetime.month,
                                 last_interval_datetime.day) \
                        + self.convert_minutes_to_timedelta(last_interval_in_min)

        return first_interval, last_interval

    def _create_new_time_period_schedule(self, charge_matrix, first_interval, last_interval):
        """Creates new charge schedules for the vehicles according to the allocated charges in the charge matrix.

        Args:
            charge_matrix: A matrix of charges allocated to the electric vehicles in each tim interval.
            first_interval: The first time interval in the scheduling window in a datetime format.
            last_interval: The last time interval in the scheduling window in a datetime format.

        Returns:
            A list of dictionaries representing a new schedule for each vehicle based on their first and last charge
            allocation in the charge matrix. Each dictionary index corresponds to a vehicle's local scheduling ID.
        """
        num_evs, num_ts = len(charge_matrix), len(charge_matrix[0])
        new_time_period = []

        for ev_i in range(num_evs):
            new_time_period.append(dict())
            # Find the time vehicle first starts charging
            curr_time = first_interval
            for ts_i in range(num_ts):
                if charge_matrix[ev_i][ts_i] > 0:
                    new_time_period[ev_i]["arrival"] = curr_time
                    break
                curr_time += timedelta(minutes=15)

            # Find the time vehicle reaches demand or stops charging
            curr_time = last_interval
            for ts_i in range(num_ts - 1, 0, -1):
                if charge_matrix[ev_i][ts_i-1] > 0:
                    new_time_period[ev_i]["departure"] = curr_time
                    break
                curr_time -= timedelta(minutes=15)

        return new_time_period

    def _add_existing_charges_to_consumption(self, timeslots, consumption):
        """Adds existing schedules' charge values as consumption to each time interval.

        Args:
            timeslots: A list of TimeSlotInfo objects.
            consumption: A list of total consumption values in each time interval.
        """
        for ts_i in range(len(timeslots)):
            for s in timeslots[ts_i].existing_schedules:
                consumption[ts_i] += s.charge

    def _get_existing_charges_as_vehicles(self, timeslots, first_interval):
        """Reconstructs each already scheduled vehicle's charge schedule as individual "vehicles" and adds them to a
        dictionary to be used as as modifiable elements in the MILP model. Updates TimeSlotInfo objects to free
        charger IDs again for allocation purposes.

        Args:
            timeslots: A list of A list of TimeSlotInfo objects.
            first_interval: The first time interval in the scheduling window in a datetime format.

        Returns:
            A dictionary representing information about vehicles already scheduled in {ev_id: VehicleInfo()} format.
        """
        scheduled_vehicles = dict()
        for ts_i in range(len(timeslots) - 1):
            next_ts_time = first_interval + timedelta(minutes=15 * (ts_i + 1))
            for s in timeslots[ts_i].existing_schedules:
                if s.ev_id not in scheduled_vehicles.keys():
                    scheduled_vehicles[s.ev_id] = VehicleInfo(s.ev_id, [s.arrival, next_ts_time],
                                                              0, 100,
                                                              0, s.charger_id)
                timeslots[ts_i].available_chargers.append(s.charger_id)
                scheduled_vehicles[s.ev_id].time_period[1] = next_ts_time
                scheduled_vehicles[s.ev_id].battery_capacity += s.charge

        return scheduled_vehicles


class LPTimeSlotOptimiser:
    """Optimiser for charge allocation (how much is put into vehicles in each time interval) modelling the problem as a
    MILP.
    """
    def __init__(self):
        self.model = Model()

    def optimise(self, unpacked_ev_info, unpacked_ts_info, charge_rates, ts_allocations, ts_interval_length,
                 existing_scheduled_evs=None, price_tariffs=None):
        """Computes the optimal allocation of charges for each vehicle in the given time intervals according to data
        on each time interval.

        Args:
            unpacked_ev_info: A dictionary of lists of data representing information on each vehicle where the index
                              represents the scheduling local ID of each vehicle.
            unpacked_ts_info: A dictionary of lists of data representing information on each time interval.
            charge_rates: A list of charging rates where their index is the charger's ID.
            ts_allocations: A time slot allocation matrix representing when vehicles can receive charges based on an
                            allocation strategy.
            ts_interval_length: The length of each time interval/slot.
            price_tariffs: The pricing tariffs associated with each time interval.
            existing_scheduled_evs: A dictionary representing information on vehicle schedules to be tweaked.
                                         Must be in the format {"unpacked_ev_info": [...], "ts_allocations": [...]}
                                         and must contain the unpacked vehicle information and the time slot allocation
                                         matrix.

        Returns:
            Two charge matrices representing the scheduling window. The first matrix represents charges for vehicles
            that have not yet been scheduled, whilst the second matrix represents charges for vehicles that had
            already been scheduled and had possibly been tweaked. Charges can be accessed using charge_matrix[i][j]
            where i is the vehicle's local ID and j is the time interval.
        """
        num_evs, num_ts = len(unpacked_ev_info["ev_ids"]), len(unpacked_ts_info["consumption"])

        if not price_tariffs:  # Default pricing tariffs
            ts_price_tariffs = [1 for ts in range(num_ts)]
        else:
            ts_price_tariffs = price_tariffs
        scheduled_vehicles = existing_scheduled_evs if existing_scheduled_evs else dict()
        charge_portion_per_interval = MINS_IN_HOUR / ts_interval_length

        charge_allocations, tweaked_charge_allocations = \
            self._allocate_charges(ev_ids=unpacked_ev_info["ev_ids"],
                                   ev_demand=unpacked_ev_info["ev_demand"],
                                   charge_rates=charge_rates,
                                   charge_battery_limit=unpacked_ev_info["charge_battery_limit"],
                                   traditional_prod=unpacked_ts_info["traditional_prod"],
                                   consumption=unpacked_ts_info["consumption"],
                                   renewables_prod=unpacked_ts_info["renewables_prod"],
                                   max_capacity=unpacked_ts_info["max_capacity"],
                                   ts_allocations=ts_allocations,
                                   price_tariffs=ts_price_tariffs,
                                   charge_portion_per_interval=charge_portion_per_interval,
                                   existing_scheduled_evs=scheduled_vehicles)

        if charge_allocations:
            charge_matrix = [[charge_allocations[ev_i][ts_i].solution_value for ts_i in range(num_ts)]
                             for ev_i in range(num_evs)]
        else:
            charge_matrix = [[0 for ts_i in range(num_ts)] for ev_i in range(num_evs)]

        if tweaked_charge_allocations:
            tweaked_charge_matrix = [[tweaked_charge_allocations[ev_i][ts_i].solution_value for ts_i in range(num_ts)]
                                     for ev_i in range(len(scheduled_vehicles["unpacked_ev_info"]["ev_ids"]))]
        else:
            tweaked_charge_matrix = [[0 for ts_i in range(num_ts)]
                                     for ev_i in range(len(scheduled_vehicles["unpacked_ev_info"]["ev_ids"]))]

        return charge_matrix, tweaked_charge_matrix

    def _allocate_charges(self, ev_ids, ev_demand, charge_rates, charge_battery_limit,
                          traditional_prod, consumption, renewables_prod, max_capacity,
                          ts_allocations, existing_scheduled_evs, price_tariffs, charge_portion_per_interval):
        """Allocates charges by using the docplex MILP model.

        Args:
            ev_ids: A list of vehicle IDs where the index represents the local scheduling ID.
            ev_demand: A list of demand of each vehicle where the index represents the local scheduling ID of the EV.
            charge_rates: A list of charge rates where the index represents the charger ID.
            charge_battery_limit: A list of charging limits for each vehicle to prevent allocation of charges that
                                  exceeds vehicles' total battery capacity. The index represents the local scheduling
                                  ID of the EV.
            traditional_prod: A list of total electricity generation by traditional sources where the index
                              represents the time slot.
            consumption: A list of total electricity consumption in the area where the index represents the time slot.
            renewables_prod: A list of total electricity generation by renewable sources where the index represents
                             the time slot.
            ts_allocations: A time slot allocation matrix representing when vehicles can receive charges based on an
                            allocation strategy.
            charge_portion_per_interval: A value that each charger rate is divided by to obtain the maximum kWh value of
                                         charging per time interval. E.g. for a time interval of 15 minutes,
                                         charging rates must be divided by 4 because 1 kW:60 minutes -> 1/4 kW:15
                                         minutes.

        Returns:
            Two matrices of decision variables representing the charging decisions for each vehicle and time slot.
            The first matrix represents the charge allocation matrix for newly scheduled vehicles and the second
            matrix represents the charge allocation matrix for vehicles that had already been scheduled,
            but had their charge allocations tweaked.
        """
        num_evs, num_ts = len(ev_ids), len(traditional_prod)
        num_existing_evs = len(existing_scheduled_evs["unpacked_ev_info"]["ev_ids"])

        self.model.clear()
        # List of decision variables representing total traditional and renewable production in each time slot
        traditional_use_decisions = [self.model.continuous_var(0, p) for p in traditional_prod]
        renewables_use_decisions = [self.model.continuous_var(0, r) for r in renewables_prod]

        # Matrix of charging decision variables
        charge_decisions, deviations_decisions = self._create_charge_and_deviation_decisions(charge_rates,
                                                                                             charge_portion_per_interval,
                                                                                             num_evs,
                                                                                             num_ts)

        # Matrix of sink variables
        sink_decisions = [self.model.continuous_var(0, self.model.infinity, name="sink" + str(ts_i))
                          for ts_i in range(num_ts)]

        # Add existing vehicles that have been scheduled to the model and make sure they meet their "demand" (i.e.
        # what their total charge already is)
        existing_schedule_charge_decisions = [[]
                                              for ev_i
                                              in range(num_existing_evs)]
        if existing_scheduled_evs:
            self._add_existing_scheduled_vehicles(existing_scheduled_evs, existing_schedule_charge_decisions,
                                                  charge_portion_per_interval, num_ts, num_existing_evs)

        # Equilibrium constraint for each time interval
        self._add_equilibrium_constraints(charge_decisions, existing_scheduled_evs, existing_schedule_charge_decisions,
                                          traditional_use_decisions, renewables_use_decisions, consumption,
                                          sink_decisions, traditional_prod, renewables_prod,
                                          num_evs, num_ts)

        # Set limits according to battery capacity, block unallocated slots and calculate total charge for each ev
        ev_total_charge = [self.model.linear_expr(name="ev_total_charge" + str(ev_i)) for ev_i in range(num_evs)]
        self._set_battery_limits_and_calc_total_charge(ts_allocations, charge_decisions, ev_total_charge,
                                                       charge_battery_limit, num_evs, num_ts)

        # For each vehicle, the charge deviations + charge allocated must be equal to the demand
        for ev_i in range(num_evs):
            self.model.add_constraint(self.model.eq_constraint(self.model.sum(deviations_decisions[ev_i])
                                                               + self.model.sum(charge_decisions[ev_i]),
                                                               ev_demand[ev_i],
                                                               name="meet_demand_ev" + str(ev_i)))

        # Total consumption in each time interval must not exceed the maximum grid capacity
        for ts_i in range(num_ts):
            self.model.add_constraint(self.model.le_constraint(traditional_use_decisions[ts_i]
                                                               + renewables_use_decisions[ts_i],
                                                               max_capacity[ts_i]))

        # The charge deviations should be minimised so it's as close to 0 as possible, the use of renewables should
        # be maximised and the prices should be minimised
        pricing_sum = self.model.linear_expr()
        deviations_sum = self.model.linear_expr()
        renewables_sum = self.model.linear_expr(-1 * self.model.sum(renewables_use_decisions))
        for ev_i in range(num_evs):
            for ts_i in range(num_ts):
                deviations_sum.add(deviations_decisions[ev_i][ts_i])
                pricing_sum.add(charge_decisions[ev_i][ts_i] * price_tariffs[ts_i])
        # Objective functions are in decreasing order
        self.model.set_lex_multi_objective("min",
                                           [deviations_sum, renewables_sum, pricing_sum],
                                           names=["charge_deviations_obj", "renewables_use_obj", "min_pricing_obj"])

        if self.model.solve():
            return charge_decisions, existing_schedule_charge_decisions
        else:
            return [], []

    def _create_charge_and_deviation_decisions(self, charge_rates, charge_portion_per_interval, num_evs, num_ts):
        charge_decisions = [[] for ev in range(num_evs)]
        deviations_decisions = [[] for ev in range(num_evs)]
        for ev_i in range(num_evs):
            for ts_i in range(num_ts):
                charge_decisions[ev_i].append(self.model.integer_var(0,
                                                                     charge_rates[ev_i] / charge_portion_per_interval,
                                                                     name="ev" + str(ev_i) + "ts" + str(ts_i)))
                # Add charge deviations (amount of charge that wasn't put into the vehicle to meet SoC demand)
                deviations_decisions[ev_i].append(self.model.continuous_var(0, self.model.infinity,
                                                                            name="ev_deviation" + str(ev_i)
                                                                                 + "ts" + str(ts_i)))

        return charge_decisions, deviations_decisions

    def _set_battery_limits_and_calc_total_charge(self, ts_allocations, charge_decisions, ev_total_charge,
                                                  charge_battery_limit, num_evs, num_ts):
        for ev_i in range(num_evs):
            for ts_i in range(num_ts):
                if not ts_allocations[ev_i][ts_i]:
                    # If the allocation matrix has a 0, make sure to block that slot for the ev decision variable
                    self.model.add_constraint(self.model.eq_constraint(charge_decisions[ev_i][ts_i],
                                                                       0,
                                                                       name="block_ev" + str(ev_i)
                                                                            + "ts" + str(ts_i)))
                else:
                    ev_total_charge[ev_i].add_term(charge_decisions[ev_i][ts_i], 1)

            # Total charge must not exceed physical limits of battery
            self.model.add_constraint(self.model.le_constraint(ev_total_charge[ev_i],
                                                               charge_battery_limit[ev_i],
                                                               name="max_charge" + str(ev_i)))

    def _add_existing_scheduled_vehicles(self, existing_scheduled_evs, existing_schedule_charge_decisions,
                                         charge_portion_per_interval, num_ts, num_existing_evs):
        for ev_i in range(num_existing_evs):
            for ts_i in range(num_ts):
                existing_schedule_charge_decisions[ev_i].append(
                    self.model.continuous_var(0,
                                              existing_scheduled_evs["unpacked_ev_info"]["charger_rates"][ev_i]
                                              / charge_portion_per_interval,
                                              name="existing_scheduled_ev" + str(ev_i) + "ts" + str(ts_i))
                )
                if existing_scheduled_evs["ts_allocations"][ev_i][ts_i] <= 0:
                    self.model.add_constraint(
                        self.model.eq_constraint(existing_schedule_charge_decisions[ev_i][ts_i],
                                                 0)
                    )
            # Make sure to give back charge already allocated; otherwise their charge may decrease
            self.model.add_constraint(
                self.model.eq_constraint(self.model.sum(existing_schedule_charge_decisions[ev_i]),
                                         existing_scheduled_evs["unpacked_ev_info"]["ev_demand"][ev_i])
            )

    def _add_equilibrium_constraints(self, charge_decisions, existing_scheduled_evs,
                                     existing_schedule_charge_decisions, traditional_use_decisions, renewables_use_decisions,
                                     consumption, sink_decisions, traditional_prod,
                                     renewables_prod, num_evs, num_ts):
        for ts_i in range(num_ts):
            # Add decision variables for ev in time interval
            ts_total_charge = self.model.linear_expr()
            for ev_i in range(num_evs):
                ts_total_charge.add_term(charge_decisions[ev_i][ts_i], 1)
            for ev_i in range(len(existing_scheduled_evs["ts_allocations"])):
                ts_total_charge.add_term(existing_schedule_charge_decisions[ev_i][ts_i], 1)

            # For each time slot, usage of generated electricity + any leftover must equal total charge + consumption
            # i.e. energy use = consumption
            self.model.add_constraint(self.model.eq_constraint(traditional_use_decisions[ts_i]
                                                               + renewables_use_decisions[ts_i],
                                                               ts_total_charge
                                                               + consumption[ts_i],
                                                               name="equilibrium" + str(ts_i)))

            # Equilibrium constraint for total consumption = total production
            self.model.add_constraint(self.model.eq_constraint(traditional_use_decisions[ts_i]
                                                               + renewables_use_decisions[ts_i]
                                                               + sink_decisions[ts_i],
                                                               traditional_prod[ts_i] + renewables_prod[ts_i]))


class LPAllocationStrategy:
    """Base strategy for allocation of time intervals for charge optimisation."""

    @abstractmethod
    def allocate(self, unpacked_ev_info, unpacked_ts_info, ts_interval_length):
        pass


class FirstChoiceAllocation(LPAllocationStrategy):
    """Allocation strategy for charging/scheduling vehicles as soon as they show up/request charging."""

    def allocate(self, unpacked_ev_info, unpacked_ts_info, ts_interval_length):
        """Creates and returns a time slot allocation matrix based on the user's choices of expected arrival and
        expected deadline/departure. In cases of conflicting charger choices, the scheduler prioritises vehicles with
        lower index positions (vehicles that appear first in the list).

        Args:
            unpacked_ev_info: A dictionary of lists of data representing information on each vehicle where the index
                              represents the scheduling local ID of each vehicle.
            unpacked_ts_info: A dictionary of lists of data representing information on each time interval.
            ts_interval_length: The length of each time interval/slot.

        Returns:
            A time slot allocation matrix that acts as a bitmask to determine which time intervals the vehicle can
            receive charges in.
        """
        num_evs, num_ts = len(unpacked_ev_info["ev_ids"]), len(unpacked_ts_info["traditional_prod"])
        first_interval = min(unpacked_ts_info["interval_start_times"])
        ts_allocations = [[0 for ts_i in range(num_ts)] for ev_i in range(num_evs)]
        available_chargers = deepcopy(unpacked_ts_info["available_chargers"])

        for ev_i in range(num_evs):
            arrival_index = (unpacked_ev_info["arrival_times"][ev_i] - first_interval) // ts_interval_length
            departure_index = (unpacked_ev_info["departure_times"][ev_i] - first_interval) // ts_interval_length

            for ts_i in range(arrival_index, departure_index):
                # If there is at least one unavailable charger, then the allocation fails
                if unpacked_ev_info["charger_ids"][ev_i] in available_chargers[ts_i]:
                    ts_allocations[ev_i][ts_i] = 1
                    available_chargers[ts_i].remove(unpacked_ev_info["charger_ids"][ev_i])
                else:
                    ts_allocations[ev_i] = [0 for ts in range(num_ts)]
                    break

        return ts_allocations


class MostRenewablesAllocation(LPAllocationStrategy):
    """Creates a time slot allocation matrix based purely on how much renewables there is in each sequence of time
    slots. The default offset for moving the arrival and departure window is 10.
    """
    def __init__(self, offset=10):
        self.offset = offset

    def allocate(self, unpacked_ev_info, unpacked_ts_info, ts_interval_length):
        """Creates and returns a time slot allocation matrix by choosing the sequence of time slots where there are
        less renewables. In cases of conflicting charger choices, the scheduler prioritises vehicles with lower index
        positions (vehicles that appear first in the list).

        Args:
            unpacked_ev_info: A dictionary of lists of data representing information on each vehicle where the index
                              represents the scheduling local ID of each vehicle.
            unpacked_ts_info: A dictionary of lists of data representing information on each time interval.
            ts_interval_length: The length of each time interval/slot.

        Returns:
            A time slot allocation matrix that acts as a bitmask to determine which time intervals the vehicle can
            receive charges in.
        """
        num_evs, num_ts = len(unpacked_ev_info["ev_ids"]), len(unpacked_ts_info["traditional_prod"])
        ts_allocations = [[0 for ts in range(num_ts)] for ev in range(num_evs)]
        first_interval = min(unpacked_ts_info["interval_start_times"])

        for ev_i in range(num_evs):
            # Get valid offsets from current arrival time
            schedule_length = (unpacked_ev_info["departure_times"][ev_i] - unpacked_ev_info["arrival_times"][ev_i]) \
                              // ts_interval_length
            arrival_ts = (unpacked_ev_info["arrival_times"][ev_i] - first_interval) // ts_interval_length
            max_ts_charge_allocation = unpacked_ev_info["charger_rates"][ev_i] / (MINS_IN_HOUR / ts_interval_length)
            ts_offsets = []
            self._add_offsets(ts_offsets, arrival_ts, schedule_length, num_ts)

            # Note that we only need to consider renewables before the departure; so do not add 1 to schedule length
            renewables_ts_totals = []
            for ts_offset_i in range(len(ts_offsets)):
                renewables_total = 0
                min_possible_charge_total = 0
                for ts_i in range(arrival_ts + ts_offsets[ts_offset_i], arrival_ts
                                                                        + ts_offsets[ts_offset_i]
                                                                        + schedule_length):
                    # If charger is not available, it is not a valid sequence of time slots so break out of loop
                    # otherwise, continue to add renewables in each time slot
                    if unpacked_ev_info["charger_ids"][ev_i] not in unpacked_ts_info["available_chargers"][ts_i]:
                        renewables_ts_totals.append(float("-inf"))
                        break
                    else:
                        renewables_total += unpacked_ts_info["renewables_prod"][ts_i]

                    # In each time interval, assume that if the vehicle can charge fully, then it does so
                    if unpacked_ts_info["renewables_prod"][ts_i] + unpacked_ts_info["traditional_prod"][ts_i] \
                            >= max_ts_charge_allocation:
                        min_possible_charge_total += max_ts_charge_allocation

                # If it's not possible fully charge to demand, then add minus infinity
                if min_possible_charge_total < unpacked_ev_info["ev_demand"][ev_i]:
                    renewables_ts_totals.append(float("-inf"))
                else:
                    renewables_ts_totals.append(renewables_total)

            best_offset = ts_offsets[renewables_ts_totals.index(max(renewables_ts_totals))]
            for ts_i in range(arrival_ts + best_offset, arrival_ts + best_offset + schedule_length):
                ts_allocations[ev_i][ts_i] = 1

        return ts_allocations

    def _add_offsets(self, ts_offsets, arrival_ts, schedule_length, num_ts):
        """Adds valid time slot offsets to offset list for a particular vehicle.

        Args:
            ts_offsets: A list of offsets.
            arrival_ts: The vehicle's arrival time slot.
            schedule_length: The supplied schedule length of a vehicle.
            num_ts: The number of time slots in the scheduling window.
        """
        for ts_offset in range(-self.offset, self.offset + 1):
            if arrival_ts + ts_offset < 0 or arrival_ts + ts_offset > num_ts - 1 - schedule_length:
                ts_offsets.append(0)
            else:
                ts_offsets.append(ts_offset)


class CheapestPricingAllocation(LPAllocationStrategy):
    """Creates a time slot allocation matrix based purely on the cost of charging in each sequence of time
    slots. The default offset for moving the arrival and departure window is 10.
    """
    def __init__(self, offset=10):
        self.offset = offset

    def allocate(self, unpacked_ev_info, unpacked_ts_info, ts_interval_length):
        """Creates and returns a time slot allocation matrix by choosing the sequence of time slots where the
        pricing tariffs are low. In cases of conflicting charger choices, the scheduler prioritises vehicles with lower
        index positions (vehicles that appear first in the list).

        Args:
            unpacked_ev_info: A dictionary of lists of data representing information on each vehicle where the index
                              represents the scheduling local ID of each vehicle.
            unpacked_ts_info: A dictionary of lists of data representing information on each time interval.
            ts_interval_length: The length of each time interval/slot.

        Returns:
            A time slot allocation matrix that acts as a bitmask to determine which time intervals the vehicle can
            receive charges in.
        """
        num_evs, num_ts = len(unpacked_ev_info["ev_ids"]), len(unpacked_ts_info["traditional_prod"])
        ts_allocations = [[0 for ts in range(num_ts)] for ev in range(num_evs)]
        first_interval = min(unpacked_ts_info["interval_start_times"])

        for ev_i in range(num_evs):
            # Get valid offsets from current arrival time
            schedule_length = (unpacked_ev_info["departure_times"][ev_i] - unpacked_ev_info["arrival_times"][ev_i]) \
                              // ts_interval_length
            arrival_ts = (unpacked_ev_info["arrival_times"][ev_i] - first_interval) // ts_interval_length
            max_ts_charge_allocation = unpacked_ev_info["charger_rates"][ev_i] / (MINS_IN_HOUR / ts_interval_length)
            ts_offsets = []
            self._add_offsets(ts_offsets, arrival_ts, schedule_length, num_ts)

            # Note that we only need to consider renewables before the departure; so do not add 1 to schedule length
            pricing_ts_total = []
            for ts_offset_i in range(len(ts_offsets)):
                pricing_total = 0
                min_possible_charge_total = 0
                for ts_i in range(arrival_ts + ts_offsets[ts_offset_i], arrival_ts
                                                                        + ts_offsets[ts_offset_i]
                                                                        + schedule_length):
                    # If charger is not available, it is not a valid sequence of time slots so break out of loop
                    # otherwise, continue to add renewables in each time slot
                    if unpacked_ev_info["charger_ids"][ev_i] not in unpacked_ts_info["available_chargers"][ts_i]:
                        pricing_ts_total.append(float("-inf"))
                        break
                    else:
                        pricing_total += unpacked_ts_info["price_tariffs"][ts_i]

                    # In each time interval, assume that if the vehicle can charge fully, then it does so
                    if unpacked_ts_info["renewables_prod"][ts_i] + unpacked_ts_info["traditional_prod"][ts_i] \
                            >= max_ts_charge_allocation:
                        min_possible_charge_total += max_ts_charge_allocation

                # If it's not possible fully charge to demand, then add minus infinity
                if min_possible_charge_total < unpacked_ev_info["ev_demand"][ev_i]:
                    pricing_ts_total.append(float("-inf"))
                else:
                    pricing_ts_total.append(pricing_total)

            best_offset = ts_offsets[pricing_ts_total.index(min(pricing_ts_total))]
            for ts_i in range(arrival_ts + best_offset, arrival_ts + best_offset + schedule_length):
                ts_allocations[ev_i][ts_i] = 1

        return ts_allocations

    def _add_offsets(self, ts_offsets, arrival_ts, schedule_length, num_ts):
        """Adds valid time slot offsets to offset list for a particular vehicle.

        Args:
            ts_offsets: A list of offsets.
            arrival_ts: The vehicle's arrival time slot.
            schedule_length: The supplied schedule length of a vehicle.
            num_ts: The number of time slots in the scheduling window.
        """
        for ts_offset in range(-self.offset, self.offset + 1):
            if arrival_ts + ts_offset < 0 or arrival_ts + ts_offset > num_ts - 1 - schedule_length:
                ts_offsets.append(0)
            else:
                ts_offsets.append(ts_offset)
