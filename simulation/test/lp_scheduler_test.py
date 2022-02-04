import unittest

from scheduler.lp_scheduler import VehicleInfo, TimeSlotInfo, LPScheduler, FirstChoiceAllocation, \
                                   MostRenewablesAllocation, CheapestPricingAllocation
from datetime import datetime, timedelta


class LPSchedulerTest(unittest.TestCase):
    @staticmethod
    def initialise_test_producers_consumers():
        """Creates test producer and consumer names for initialising LPScheduler.

        Returns:
            A tuple in the format (traditional_producers, consumers, renewables_producers)
        """
        return ["Coal", "Gas"], ["All Consumption"], ["Solar"]

    @staticmethod
    def initialise_vehicles_with_same_data(num_evs, arrival_soc, soc_demand,
                                           battery_capacity, requested_start, requested_deadline):
        """Creates vehicles that have the same requested charge/time period, arrival and departure SoCs,
        and battery capacity. All vehicles will have unique vehicle IDs and will each use a unique charger.

        Notes:
            The number of vehicles must be the same as the number of chargers.

        Args:
            num_evs: The number of vehicles to be initialised.
            arrival_soc: The arrival state of charge of all vehicles to be initialised.
            soc_demand: The state of charge at the end of the charging period of all vehicles to be initialised.
            battery_capacity: The battery capacity of all vehicles to be initialised.
            requested_start: The requested start charge time of all vehicles to be initialised.
            requested_deadline: The requested end charge time of all vehicles to be initialised.

        Returns:
            A list of VehicleInfo objects that have the same time period, arrival SoC, SoC demand, and battery
            capacity. All vehicles will use a unique charger.
        """
        vehicles = []
        for ev_i in range(num_evs):
            vehicles.append(VehicleInfo(ev_id=ev_i,
                                        time_period=(requested_start, requested_deadline),
                                        arrival_soc=arrival_soc,
                                        soc_demand=soc_demand,
                                        battery_capacity=battery_capacity,
                                        charger_id=ev_i))

        return vehicles

    @staticmethod
    def get_timeslot_allocation_for_test(vehicles, timeslots, allocation_strat=None):
        """A method that allows access to 'non-public' variables and methods in LPScheduler to be used for testing
        time slot allocation.

        Args:
            vehicles: A list of VehicleInfo objects to allocate time slots for.
            timeslots: A list of TimeSlotInfo objects representing the scheduling window.
            allocation_strat: The time slot allocation strategy to be used.

        Returns:
            A time slot allocation matrix that acts as a bitmask to determine which time intervals the vehicle can
            receive charges in.
        """
        allocation_strategy = FirstChoiceAllocation() if allocation_strat is None else allocation_strat

        trad_producers, consumers, renewables_producers = LPSchedulerTest.initialise_test_producers_consumers()
        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, [5],
                                allocation_strategy=allocation_strategy)
        unpacked_ev_info = scheduler._convert_vehicles_info_to_lists(vehicles, timeslots[0].date_time)
        unpacked_ts_info = scheduler._convert_timeslots_info_to_lists(timeslots)

        return scheduler._allocator.allocate(unpacked_ev_info, unpacked_ts_info, scheduler.interval_length)

    def test_charges_vehicles_to_demand(self):
        """LPS 1.1

        The scheduler should attempt to charge the vehicles up to their chosen charge level.
        Given that full charging is possible with the circumstances, by the end of each vehicle’s charging period, these
        must have been charged to the charge they have chosen before scheduling.

        Test Method:
            Assume in this test that there is enough generated electricity (30 kWh) from traditional and renewable
            sources in 3 time intervals (A charge period of 30 minutes). Three vehicles are to be scheduled,
            each having a raw demand of 10 kWh. All three use a charger with a charge rate of 50 kW.

        Expected:
            All vehicles get a total charge of 10 kWh that has been requested.
        """
        num_evs = 3
        num_ts = 3
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        available_chargers = list(range(num_evs))
        charger_rates = [50 for c in available_chargers]
        requested_start = datetime(2021, 5, 25, hour=15)
        requested_deadline = datetime(2021, 5, 25, hour=15, minute=30)

        # Suppose there were num_evs number of vehicles, and that they all require 10 kWh
        vehicles = self.initialise_vehicles_with_same_data(num_evs=num_evs,
                                                           arrival_soc=50,
                                                           soc_demand=60,
                                                           battery_capacity=100,
                                                           requested_start=requested_start,
                                                           requested_deadline=requested_deadline)

        timeslot1 = TimeSlotInfo(date_time=requested_start, traditional_prod=10,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=available_chargers)
        timeslot2 = TimeSlotInfo(date_time=requested_start + timedelta(minutes=15),
                                 traditional_prod=20,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=available_chargers)
        timeslot3 = TimeSlotInfo(date_time=requested_deadline,
                                 traditional_prod=10,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[])

        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule(vehicles, [timeslot1, timeslot2, timeslot3])

        self.assertTrue(
            all(map(lambda c: c == 10, [schedule.get_schedules()[ev]["charge"] for ev in range(num_ts)]))
        )

    def charges_vehicles_close_to_demand(self):
        """LPS1.2

        The scheduler should attempt to charge the vehicles up to their chosen charge level. If it is not realistically
        possible to do this (e.g., not enough electricity generated), the scheduler should still schedule the vehicles,
        charging the vehicles for as much as possible.

        Test Method:
            Assume in this test that there is not enough generated electricity for the vehicles' demand. Suppose all
            vehicles had a total demand of 30 kWh, but in the scheduling window of three intervals, there are only 20
            kWh available in total.

        Expected:
            Vehicles should still get some sort of charge.
        """
        num_evs = 3
        num_ts = 3
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        available_chargers = list(range(num_evs))
        charger_rates = [50 for c in available_chargers]
        requested_start = datetime(2021, 5, 25, hour=15)
        requested_deadline = datetime(2021, 5, 25, hour=15, minute=30)

        vehicles = self.initialise_vehicles_with_same_data(num_evs=num_evs,
                                                           arrival_soc=50,
                                                           soc_demand=60,
                                                           battery_capacity=100,
                                                           requested_start=requested_start,
                                                           requested_deadline=requested_deadline)

        timeslot1 = TimeSlotInfo(date_time=requested_start, traditional_prod=10,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=available_chargers)
        timeslot2 = TimeSlotInfo(date_time=requested_start + timedelta(minutes=15),
                                 traditional_prod=10,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=available_chargers)
        timeslot3 = TimeSlotInfo(date_time=requested_deadline,
                                 traditional_prod=10,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[])

        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule(vehicles, [timeslot1, timeslot2, timeslot3])

        # All vehicles should be allocated charge, no matter how little.
        self.assertTrue(
            all(map(lambda c: c > 0, [schedule.get_schedules()[ev]["charge"] for ev in range(num_ts)]))
        )

    def test_fair_charging(self):
        """LPS1.3

        Given a number of vehicles that are to be scheduled in one go, if there is not enough electricity generated to
        fully charge all of them, the scheduler should attempt to distribute the charges fairly.
        Note: Due to the nature of charges being integers, this only tests for certain cases (e.g., where balance can be
         achieved). This is because it is difficult to predict how the solver will handle every case.

        Test Method:
            Assume that two vehicles are to be scheduled: one requires 50 kWh worth of charge and the other requires
            only 20 kWh. Suppose that the scheduling window had three time slots, with time slot 1 and 2 having only
            10 kWh production each.

        Expected:
            Vehicles should get 10 kWh charge each.
        """
        num_evs = 2
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        charger_rates = [50, 50]
        requested_start = datetime(2021, 5, 25, hour=15)  # Users 1 and 2 expects to arrive at 3:00
        requested_deadline = datetime(2021, 5, 25, hour=15, minute=30)  # Users 1 and 2 want to charge by 3:15

        vehicles = self.initialise_vehicles_with_same_data(num_evs=num_evs,
                                                           arrival_soc=50,
                                                           soc_demand=100,
                                                           battery_capacity=100,
                                                           requested_start=requested_start,
                                                           requested_deadline=requested_deadline)

        timeslot1 = TimeSlotInfo(date_time=requested_start, traditional_prod=20,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[0, 1])
        timeslot2 = TimeSlotInfo(date_time=requested_start + timedelta(minutes=15),
                                 traditional_prod=20,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[0, 1])
        timeslot3 = TimeSlotInfo(date_time=requested_deadline,
                                 traditional_prod=0,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[])

        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule(vehicles, [timeslot1, timeslot2, timeslot3])

        self.assertTrue(schedule.get_schedules()[0]["charge"] == schedule.get_schedules()[1]["charge"])

    def test_should_not_schedule_if_no_available_production(self):
        """LPS 1.4

        The consumption of the charging station for a given time slot cannot exceed the energy production at that time.
        The scheduler should not schedule another vehicle in a time slot where this would happen, even if there is a
        charging point available within the station.

        Test Method:
            Schedule two vehicles where all time slots in the scheduling window have production equal to consumption..

        Expected Result:
            The returned Timetable should be empty.
        """
        num_evs = 2
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        charger_rates = [50, 50]
        requested_start = datetime(2021, 5, 25, hour=15)  # Users 1 and 2 expects to arrive at 3:00
        requested_deadline = datetime(2021, 5, 25, hour=15, minute=30)  # Users 1 and 2 wants to charge by 3:15

        vehicles = self.initialise_vehicles_with_same_data(num_evs=num_evs,
                                                           arrival_soc=50,
                                                           soc_demand=100,
                                                           battery_capacity=100,
                                                           requested_start=requested_start,
                                                           requested_deadline=requested_deadline)

        timeslot1 = TimeSlotInfo(date_time=requested_start, traditional_prod=20,
                                 consumption=20,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[0, 1])
        timeslot2 = TimeSlotInfo(date_time=requested_start + timedelta(minutes=15),
                                 traditional_prod=20,
                                 consumption=20,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[0, 1])
        timeslot3 = TimeSlotInfo(date_time=requested_deadline,
                                 traditional_prod=0,
                                 consumption=0,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[])

        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule(vehicles, [timeslot1, timeslot2, timeslot3])

        self.assertTrue(not schedule.get_schedules())

    def test_prioritises_renewables(self):
        """LPS 2.1

        The scheduler should maximise the use of renewable electricity, charging only in time intervals where
        there is enough electricity from renewable sources generated.

        Test Method:
            Assume in this test (a charge period of 30 minutes) that there is enough renewable electricity in the first
            time interval for this to be possible, and assume that no renewable electricity is generated in the second
            time interval.

        Expected:
            The scheduler should then only charge the vehicles in the first time interval; no vehicles should be
            scheduled during the second time interval.
        """
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        charger_rates = [50, 50]
        requested_start = datetime(2021, 5, 25, hour=15)  # Users 1 and 2 expects to arrive at 3:00
        requested_deadline = datetime(2021, 5, 25, hour=15, minute=30)  # Users 1 and 2 wants to charge by 3:15

        vehicle1 = VehicleInfo(ev_id=0,
                               time_period=(requested_start, requested_deadline),
                               arrival_soc=50,
                               soc_demand=60,
                               battery_capacity=100,
                               charger_id=0)

        vehicle2 = VehicleInfo(ev_id=1,
                               time_period=(requested_start, requested_deadline),
                               arrival_soc=50,
                               soc_demand=60,
                               battery_capacity=100,
                               charger_id=1)

        timeslot1 = TimeSlotInfo(date_time=requested_start, traditional_prod=20,
                                 consumption=10,
                                 renewables_prod=30,
                                 max_capacity=float("inf"),
                                 available_chargers=[0, 1])
        timeslot2 = TimeSlotInfo(date_time=requested_start + timedelta(minutes=15),
                                 traditional_prod=20,
                                 consumption=10,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[0, 1])
        timeslot3 = TimeSlotInfo(date_time=requested_deadline,
                                 traditional_prod=20,
                                 consumption=10,
                                 renewables_prod=0,
                                 max_capacity=float("inf"),
                                 available_chargers=[])

        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule([vehicle1, vehicle2], [timeslot1, timeslot2, timeslot3])

        self.assertTrue(schedule.get_schedules()[0]["arrival"] == requested_start
                        and schedule.get_schedules()[0]["departure"] == timeslot2.date_time
                        and schedule.get_schedules()[1]["arrival"] == requested_start
                        and schedule.get_schedules()[1]["departure"] == timeslot2.date_time)

    def test_schedule_saves_money(self):
        """LPS2.2

        The scheduler should choose the time slots a lower charging cost.

        Test Method:
            Assume that a vehicle requested to charge for an hour and a half (7 time slots, taking into account the
            last time slot). Suppose that sit had a charge demand of 30 kWh, and that all time slots have 10 kWh
            available electricity each, with 3 time slots having 14p charging cost and the other 4 having 14.23p
            charging cost.

        Expected Result:
            The vehicle is charged during the time slots with 14p charging cost.
        """
        num_ts = 7
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        charger_rates = [50]
        requested_start = datetime(2021, 5, 25, hour=15)
        requested_deadline = datetime(2021, 5, 25, hour=15) + timedelta(minutes=6*15)
        tariffs = [14.0 for p in range(3)] + [14.23 for p in range(4)]

        vehicles = [VehicleInfo(ev_id=1,
                                time_period=(requested_start, requested_deadline),
                                arrival_soc=0,
                                soc_demand=100,
                                battery_capacity=30,
                                charger_id=0)]

        timeslots = []
        for ts_i in range(num_ts):
            timeslots.append(TimeSlotInfo(date_time=requested_start + timedelta(minutes=15*ts_i),
                                          traditional_prod=10,
                                          consumption=0,
                                          renewables_prod=0,
                                          max_capacity=float("inf"),
                                          available_chargers=[0],
                                          price_tariff=tariffs[ts_i]))

        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule(vehicles, timeslots)

        self.assertTrue(all([schedule.timetable[ts_i][0].charge > 0 for ts_i in range(3)]))

    def test_valid_timeslot_info(self):
        """LPS3.1

        Entering valid construction arguments for TimeSlotInfo should pass the validation method.

        Test Method:
            For this test, test the validation method of TimeSlotInfo. Normal use (that is, through the scheduler
            interface) should automatically validate this normally as the scheduler uses parameter objects' validation
            methods. The validation method for TimeSlotInfo is simple, as each object itself can only check for
            negative values.

        Expected Result:
            The validation method returns a signifier to represent valid data passed into the constructor.
        """
        date_time = datetime.now()
        trad_prod = renewable_prod = consumption = 0
        max_capacity = 50
        timeslot = TimeSlotInfo(date_time=date_time,
                                traditional_prod=trad_prod,
                                renewables_prod=renewable_prod,
                                consumption=consumption,
                                max_capacity=max_capacity,
                                available_chargers=[])

        self.assertTrue(timeslot.is_valid())

    def test_invalid_timeslot_info(self):
        """LPS3.2

        Entering invalid construction arguments for TimeSlotInfo should fail the validation method.

        Test Method:
            For this test, test the validation method of TimeSlotInfo AND the use of validation through the scheduler
            interface. Should one attempt to schedule with invalid data, the scheduler will return None.

        Expected Result:
            The validation method returns a signifier to represent invalid data passed into the constructor and the
            scheduler returns None to handle the invalid data.
        """
        num_ts = 5
        trad_producers, consumers, renewables_producers = self.initialise_test_producers_consumers()
        charger_rates = [7]
        requested_start = datetime(2021, 5, 25, hour=15)
        requested_deadline = datetime(2021, 5, 25, hour=15) + timedelta(minutes=num_ts*15)
        times = [datetime(2021, 5, 25, hour=15) + timedelta(minutes=15*ts_i) for ts_i in range(num_ts)]
        trad_prod = renewable_prod = consumption = -5
        max_capacity = 50

        vehicles = [VehicleInfo(ev_id=1,
                                time_period=(requested_start, requested_deadline),
                                arrival_soc=0,
                                soc_demand=100,
                                battery_capacity=30,
                                charger_id=0)]

        timeslots = []
        for ts_i in range(num_ts):
            timeslots.append(TimeSlotInfo(date_time=times[ts_i],
                                          traditional_prod=trad_prod,
                                          renewables_prod=renewable_prod,
                                          consumption=consumption,
                                          max_capacity=max_capacity,
                                          available_chargers=[]))
        scheduler = LPScheduler(trad_producers, consumers, renewables_producers, charger_rates)
        schedule = scheduler.schedule(vehicles, timeslots)

        self.assertTrue(all([not ts.is_valid() for ts in timeslots])
                        and schedule is None)

    def test_first_choice_uses_requested_times(self):
        """LPS4.1

        The first choice allocation strategy allocates time slots based on the requested time period.

        Test Method:
            Supply a scheduling window with 10 time slots and given a vehicle, apply first choice with the arrival as
            first time slot and the deadline/departure as the last time slot.

        Expected Result:
            A time slot allocation matrix with all columns (apart from the last one) filled with 1s is returned by the
            allocate method.
        """
        window_length = 10
        window_start = datetime(2021, 5, 25)
        window_end = window_start + timedelta(minutes=15*(window_length-1))
        vehicles = [VehicleInfo(ev_id=0,
                                time_period=(window_start, window_end),
                                arrival_soc=0,
                                soc_demand=100,
                                battery_capacity=27,
                                charger_id=0)]
        timeslots = []
        for ts_i in range(window_length):
            timeslots.append(TimeSlotInfo(window_start + timedelta(minutes=15*ts_i),
                                          traditional_prod=5,
                                          consumption=2,
                                          renewables_prod=0,
                                          max_capacity=30,
                                          available_chargers=[0]))

        ts_alloc_matrix = self.get_timeslot_allocation_for_test(vehicles, timeslots)
        expected_ts_alloc_matrix = [[1 for ts_i in range(window_length-1)] + [0]]

        self.assertEqual(expected_ts_alloc_matrix, ts_alloc_matrix)

    def test_most_renewables_chooses_ts_with_max_renewables_sum(self):
        """LPS4.2

        The most renewables allocation strategy allocates time slots with the highest sum of renewables production.

        Test Method:
            Supply a scheduling window with 10 time slots and given a vehicle, apply most renewables with the arrival as
            first time slot and the deadline/departure as the fourth time slot. Have the last four time slots'
            production of renewables sum to the highest of any four sequences of time slots in the scheduling window.

        Expected Result:
            A time slot allocation matrix with elements 6, 7, and 8 having an integer value of 1 is returned by the
            allocate method (keeping in mind that the last time slot cannot be a valid allocation because it is used
            as the 'end of charge'/departure time slot).
        """
        window_length = 10
        window_start = datetime(2021, 5, 25)
        vehicles = [VehicleInfo(ev_id=0,
                                time_period=(window_start, window_start + timedelta(minutes=45)),
                                arrival_soc=90,
                                soc_demand=100,
                                battery_capacity=27,
                                charger_id=0)]
        ts_renewables = [5, 5, 10, 22, 12, 5, 6, 30, 12, 10]
        timeslots = []
        for ts_i in range(window_length):
            timeslots.append(TimeSlotInfo(window_start + timedelta(minutes=15*ts_i),
                                          traditional_prod=5,
                                          consumption=2,
                                          renewables_prod=ts_renewables[ts_i],
                                          max_capacity=30,
                                          available_chargers=[0]))

        ts_alloc_matrix = self.get_timeslot_allocation_for_test(vehicles,
                                                                timeslots,
                                                                allocation_strat=MostRenewablesAllocation())
        expected_ts_alloc_matrix = [[0 for ts_i in range(window_length-1)] + [0]]
        expected_ts_alloc_matrix[0][6] = expected_ts_alloc_matrix[0][7] = expected_ts_alloc_matrix[0][8] = 1

        self.assertEqual(expected_ts_alloc_matrix, ts_alloc_matrix)

    def test_cheapest_pricing_chooses_ts_with_cheapest_cost(self):
        """LPS4.3

        The cheapest pricing allocation strategy allocates time slots with the lowest sum of price tariffs.

        Test Method:
            Supply a scheduling window with 10 time slots and given a vehicle, apply cheapest pricing with the
            arrival as first time slot and the deadline/departure as the fourth time slot. Have the last four time
            slots' price tariff sum to the lowest of any four sequences of time slots in the scheduling window.

        Expected Result:
            A time slot allocation matrix with elements 6, 7, and 8 having an integer value of 1 is returned by the
            allocate method (keeping in mind that the last time slot cannot be a valid allocation because it is used
            as the 'end of charge'/departure time slot).
        """
        window_length = 10
        window_start = datetime(2021, 5, 25)
        vehicles = [VehicleInfo(ev_id=0,
                                time_period=(window_start, window_start + timedelta(minutes=45)),
                                arrival_soc=90,
                                soc_demand=100,
                                battery_capacity=27,
                                charger_id=0)]
        ts_price_tariff = [30, 30, 21, 25, 25, 26, 15, 15, 15, 15]
        timeslots = []
        for ts_i in range(window_length):
            timeslots.append(TimeSlotInfo(window_start + timedelta(minutes=15*ts_i),
                                          traditional_prod=5,
                                          consumption=2,
                                          renewables_prod=5,
                                          max_capacity=30,
                                          price_tariff=ts_price_tariff[ts_i],
                                          available_chargers=[0]))

        ts_alloc_matrix = self.get_timeslot_allocation_for_test(vehicles,
                                                                timeslots,
                                                                allocation_strat=CheapestPricingAllocation())
        expected_ts_alloc_matrix = [[0 for ts_i in range(window_length-1)] + [0]]
        expected_ts_alloc_matrix[0][6] = expected_ts_alloc_matrix[0][7] = expected_ts_alloc_matrix[0][8] = 1

        self.assertEqual(expected_ts_alloc_matrix, ts_alloc_matrix)


if __name__ == "__main__":
    unittest.main()
