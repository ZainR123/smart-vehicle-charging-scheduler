"""Informal testing attempts for the LP Scheduler. Unit tests are preferable."""

import time
import random
import math
import csv

from scheduler.lp_scheduler import TimeSlotInfo, ScheduleInfo, FirstChoiceAllocation, MostRenewablesAllocation, \
                                   CheapestPricingAllocation, LPScheduler, VehicleInfo

from datetime import timedelta
from datetime import datetime

BATTERY_CAPACITIES = [200, 120, 115, 110, 100, 95, 90, 88, 87, 86.5, 85, 84.7, 83.7, 80, 77, 76, 75, 74, 72, 71,
                      70, 68, 66.5, 64.7, 64, 63, 58, 56, 52, 50, 48.8, 45, 42.5, 39.2, 38.3, 38, 37.9, 37.3, 36,
                      32.3, 31, 30, 28.9, 28.5, 26.8, 23.8, 16.7]


def test_optimise_random():
    day = 5
    month = 3
    year = 2021
    charging_rates = [6, 7, 22, 50, 43]
    num_ts = 192  # Including the departure time
    num_evs = 20
    num_chargers = num_evs  # Assume each there's a charger for each vehicle

    num_of_days = math.ceil(num_ts / 96)
    days = [day + d for d in range(0, num_of_days)]
    time_period = list()
    for d in days:
        for h in range(0, 24):
            for m in (0, 15, 30, 45):
                time_period.append(datetime(year, month, d, hour=h, minute=m))

    producers = ["Producer 1", "Producer 2"]
    sample_production = [[random.randint(10, 20) for ts in range(num_ts)] for p in producers]

    consumers = ["Consumer 1", "Consumer 2"]
    sample_consumption = [[random.randint(5,20) for ts in range(num_ts)] for c in consumers]

    renewable_producers = ["Renewable Producer 1"]
    sample_renewables = [[random.randint(10, 20) for ts in range(num_ts)] for r in renewable_producers]

    ts_total_production = []
    ts_total_consumption = []
    ts_total_renewables = []
    for ts_i in range(num_ts):
        prod_sum = 0
        renewable_sum = 0
        for p_id in range(len(sample_production)):
            prod_sum += sample_production[p_id][ts_i]
        for r_id in range(len(sample_renewables)):
            prod_sum += sample_renewables[r_id][ts_i]
            renewable_sum += sample_renewables[r_id][ts_i]

        consume_sum = 0
        for c_id in range(len(sample_consumption)):
            consume_sum += sample_consumption[c_id][ts_i]

        ts_total_production.append(prod_sum)
        ts_total_consumption.append(consume_sum)
        ts_total_renewables.append(renewable_sum)

    charger_rates = [random.choice(charging_rates) for charger in range(num_chargers)]

    vehicle_ids = list(range(25, 25 + num_evs))  # example: suppose vehicles' ids start from 25
    vehicle_times = []
    vehicle_socs = []
    vehicle_capacities = []
    vehicle_charger_allocations = [c for c in range(num_chargers)]
    for ev_i in range(num_evs):
        arrival_soc = random.randint(50, 70)
        departure_soc = random.randint(arrival_soc, 100)
        vehicle_socs.append([arrival_soc, departure_soc])
        vehicle_capacities.append(random.choice(BATTERY_CAPACITIES))

        required_charge = (departure_soc - arrival_soc) / 100 * vehicle_capacities[ev_i]
        charger_rate_limit = charger_rates[ev_i] / 4
        minimum_timeslots = required_charge // charger_rate_limit if required_charge >= charger_rate_limit else 1

        # Generate arrival and departure in minutes (no vehicle should arrive at the last time interval,
        # hence the -30 when generating the arrival! Otherwise, it would mean that the vehicle arrives at the last
        # interval that the scheduling is considering, but then departs at the same time (allocator will give an
        # error)...)
        # num_ts minus one because 0 counts as an interval, and num_ts by its own will cause the generated times to
        # exceed by 15 minutes.
        # Also, since everything's randomly generated, arrival might make it so that there's not enough time
        # intervals to meet demand (if num of ts is too low, this can happen)
        arrival = random.randint(0, (num_ts-1) * 15 - 15 - minimum_timeslots * 15) \
            if (num_ts-1) * 15 - 15 - minimum_timeslots * 15 >= 0 else random.randint(0, ((num_ts-1) * 15 - 15))

        departure = random.randint(min(arrival + minimum_timeslots * 15, (num_ts-1) * 15), (num_ts-1) * 15)

        # Use as offsets for datetime arrival and departure
        da = timedelta(hours=(arrival // 60), minutes=(arrival / 60 % 1) * 60)
        dd = timedelta(hours=(departure // 60), minutes=(departure / 60 % 1) * 60)

        arrival = datetime(year, month, day) + da
        departure = datetime(year, month, day) + dd

        vehicle_times.append((arrival, departure))

    ts_max_capacity = [float("inf") for ts_i in range(num_ts)]
    # ts_max_capacity = [p + random.randint(0, 5) for p in sample_production]
    for ts_i in range(num_ts):
        # ts_max_capacity[ts_i] = (ts_total_production[ts_i] + ts_total_renewables[ts_i]) * random.uniform(0.7,
        #                                                                                                  0.8) + \
        #                         (ts_total_production[ts_i] + ts_total_renewables[ts_i]) * random.uniform(0, 0.2)t
        ts_max_capacity[ts_i] = 1000

    vehicles = []
    timeslots = []
    for ts_i in range(num_ts):
        timeslot = TimeSlotInfo(time_period[ts_i], ts_total_production[ts_i],
                                ts_total_consumption[ts_i], ts_total_renewables[ts_i],
                                ts_max_capacity[ts_i], vehicle_charger_allocations.copy(),
                                [])
        timeslots.append(timeslot)

    for ev_i in range(num_evs):
        vehicle = VehicleInfo(ev_id=vehicle_ids[ev_i], time_period=vehicle_times[ev_i],
                              arrival_soc=vehicle_socs[ev_i][0],
                              soc_demand=vehicle_socs[ev_i][1], battery_capacity=vehicle_capacities[ev_i],
                              charger_id=vehicle_charger_allocations[ev_i])
        vehicles.append(vehicle)

    scheduler = LPScheduler(producers, consumers, renewable_producers, charger_rates,
                            allocation_strategy=MostRenewablesAllocation())
    schedule = scheduler.schedule(vehicles, timeslots)

    print("\n")
    for ts in schedule.timetable:
        for si in ts:
            print("Vehicle {}, Charge for {} kWh, Using Charger {}, Charge Limit {} Arriving at day {} at {}th "
                  "minute, Departing at day {} at {}th minute."
                  .format(si.ev_id, si.charge, si.charger_id, charger_rates[si.charger_id] / 4, si.arrival.day,
                          si.arrival.hour * 60 + si.arrival.minute,
                          si.departure.day,
                          si.departure.hour * 60 + si.departure.minute))

    returned_schedule = schedule.get_schedules()
    print("Schedule in dictionary format:", returned_schedule)

    for ev_id in range(25, 25 + num_evs):
        if ev_id not in returned_schedule:
            print("Demand for {}: {} | No. of time slots: {})"
                  .format(ev_id,
                          (vehicle_socs[ev_id-25][1] - vehicle_socs[ev_id-25][0]) / 100 * vehicle_capacities[ev_id-25],
                          (vehicle_times[ev_id-25][1] - vehicle_times[ev_id-25][0]) / 15))
            print(ev_id, "not scheduled!")
            if vehicle_times[ev_id-25][1] == vehicle_times[ev_id-25][0]:
                print("Arrival same as departure")
        else:
            first_arrival = scheduler.discretise_time(min(timeslots[ev_i].date_time.hour * 60 + timeslots[
                ev_i].date_time.minute for ev_i in range(num_ts)))
            arrival = (returned_schedule[ev_id]["arrival"].hour * 60 + returned_schedule[ev_id]["arrival"].minute
                       - first_arrival) // 15
            departure = (returned_schedule[ev_id]["departure"].hour * 60 + returned_schedule[ev_id]["departure"].minute
                         - first_arrival) // 15
            print("EV {}: Charge: {}, Demand {}, Charge Rate Limit {} | Arrival {} Departure {}"
                  .format(ev_id, returned_schedule[ev_id]["charge"],
                          math.floor((vehicle_socs[ev_id - 25][1] - vehicle_socs[ev_id - 25][0]) / 100 * vehicle_capacities[ev_id - 25]),
                          charger_rates[ev_id-25] / 4,
                          arrival,
                          departure))

    charges = [0 for ts in range(num_ts)]
    for ts_i in range(num_ts):
        for si in schedule.timetable[ts_i]:
            charges[ts_i] += si.charge

    with open("test_lp_temp.csv", "w", newline="") as result_file:
        wr = csv.writer(result_file, delimiter=",")
        for (p, ac, ev_c, cap) in zip([ts_total_production[ts_i] + ts_total_renewables[ts_i] for ts_i in range(num_ts)],
                                    ts_total_consumption,
                                    charges,
                                    ts_max_capacity):
            wr.writerow((p, ac, ev_c, cap, ac + ev_c))
    for ts_i in range(num_ts):
        if ts_total_consumption[ts_i] > ts_total_production[ts_i] + ts_total_renewables[ts_i]:
            print("Consumption greater than production")

    print("Scheduler status codes", schedule.get_schedule_status())

def test_optimise():
    #
    # ---------------------------------------------------------------------------------------------------------------
    # Categorising production, consumption and renewables from caller code
    # ---------------------------------------------------------------------------------------------------------------
    #

    # E.g., 900 - 975 (min) = 15:00 - 16:15
    # number of timeslots to give is (departure - arrival) / 15 + 1 where 1 is added to take into account the departure
    num_ts = 6  # IMPORTANT: Make sure the matrices have the same number of columns
    num_evs = 4
    year = 2021
    month = 3
    day = 5

    # In a static context, this is what the caller (simulation?) could do to represent individual sources--which
    # produces and which consumes electricity
    producers = ["Coal 1", "Natural Gas 1", "Coal 2", "Oil 1"]  # Then id of coal electricity generator is 0 and so on

    # Could then represent individual production over time intervals as matrix
    sample_production = [[10, 20, 25, 18, 17, 18],     # Production of coal fired power stations over 5 intervals
                         [10, 15, 20, 25, 20, 15],
                         [20, 15, 20, 20, 21, 20],
                         [5, 10, 2, 3, 6, 5]]     # Production of natural gas power stations over 4 intervals

    # Structure would then be the same for consumption. Suppose we can adjust how much is consumed by the category of
    # electricity use--essential and non-essential
    consumers = ["Essential", "Non-essential"]

    # Then do the same for consumption
    sample_consumption = [[10, 5, 3, 6, 10, 10],       # Consumption of electricity for essential needs
                          [5, 10, 11, 15, 6, 10]]      # Consumption of electricity for non-essential tasks,
                                                       # e.g. entertainment

    renewable_producers = ["Solar 1", "Solar 2", "Nuclear"]  # Renewable energy producers

    # Do the same again for renewable energy producers
    sample_renewables = [[5, 5, 10, 5, 5, 10],
                         [3, 10, 2, 10, 8, 2],
                         [5, 5, 5, 5, 5, 5]]

    # Charging points represented as a list where the index is the charger ID and the item is the charge rate
    charger_rates = [50, 50, 50, 50]  # Assume four 50kW chargers

    vehicle_ids = [0, 25, 60, 120]
    vehicle_times = [(datetime(year, month, day, hour=15, minute=15), datetime(year, month, day, hour=16, minute=20)),
                     (datetime(year, month, day, hour=14, minute=57), datetime(year, month, day, hour=16, minute=8)),
                     (datetime(year, month, day, hour=15, minute=45), datetime(year, month, day, hour=16, minute=15)),
                     (datetime(year, month, day, hour=15, minute=30), datetime(year, month, day, hour=16, minute=0))]
    vehicle_socs = [(60, 80), (20, 50), (50, 100), (64, 80)]
    vehicle_capacities = [30, 40, 30, 30]
    vehicle_charger_allocations = [0, 1, 2, 3]
    time_period = [datetime(year, month, day, hour=15) + timedelta(minutes=15*i) for i in range(0, 6)]
    ts_max_capacity = [p + random.randint(0, 5) for p in range(num_ts)]

    # To then sum total production and consumption at each time slot for the scheduler:
    ts_total_production = []
    ts_total_consumption = []
    ts_total_renewables = []
    for ts_i in range(num_ts):
        prod_sum = 0
        renewable_sum = 0
        for p_id in range(len(sample_production)):
            prod_sum += sample_production[p_id][ts_i]
        for r_id in range(len(sample_renewables)):
            prod_sum += sample_renewables[r_id][ts_i]
            renewable_sum += sample_renewables[r_id][ts_i]

        consume_sum = 0
        for c_id in range(len(sample_consumption)):
            consume_sum += sample_consumption[c_id][ts_i]

        ts_total_production.append(prod_sum)
        ts_total_consumption.append(consume_sum)
        ts_total_renewables.append(renewable_sum)

    vehicles = []
    timeslots = []
    for ts_i in range(num_ts):
        timeslot = TimeSlotInfo(time_period[ts_i], ts_total_production[ts_i],
                                ts_total_consumption[ts_i], ts_total_renewables[ts_i],
                                ts_max_capacity[ts_i], [0, 1, 2, 3],
                                [])
        timeslots.append(timeslot)

    for ev_i in range(num_evs):
        vehicle = VehicleInfo(ev_id=vehicle_ids[ev_i], time_period=vehicle_times[ev_i],
                              arrival_soc=vehicle_socs[ev_i][0], soc_demand=vehicle_socs[ev_i][1],
                              battery_capacity=vehicle_capacities[ev_i],
                              charger_id=vehicle_charger_allocations[ev_i])
        vehicles.append(vehicle)

    sample_existing_schedule = [ScheduleInfo(200, 2, 2, datetime(year, month, day, hour=15, minute=15),
                                             datetime(year, month, day, hour=15, minute=45))]
    sample_existing_schedule_2 = [ScheduleInfo(200, 2, 2, datetime(year, month, day, hour=15, minute=15),
                                             datetime(year, month, day, hour=15, minute=45))]
    timeslots[1].existing_schedules, timeslots[2].existing_schedules = sample_existing_schedule, \
                                                                       sample_existing_schedule_2

    scheduler = LPScheduler(producers, consumers, renewable_producers, charger_rates,
                            allocation_strategy= MostRenewablesAllocation())
    schedule = scheduler.schedule(vehicles, timeslots)
    print(schedule.get_schedules())
    print("\n")
    for ts in schedule.timetable:
        for si in ts:
            print("Vehicle {}, Charge for {} kWh, Using Charger {}, Arriving at day {} at {}th minute, Departing at "
                  "day {} at {}th minute."
                  .format(si.ev_id, si.charge, si.charger_id, si.arrival.day, si.arrival.hour * 60 + si.arrival.minute,
                          si.departure.day,
                          si.departure.hour * 60 + si.departure.minute))

    # print()
    # for ev_i in range(num_evs):
    #     print("EV {}".format(vehicle_ids[ev_i]).ljust(8), end=" || ")
    #     for ts_i in range(num_ts):
    #         print("{}".format(schedule.timetable[ev_i][ts_i]).center(7), end=" | ")
    #     print("Demand: {}".format((vehicle_socs[ev_i][1] - vehicle_socs[ev_i][0]) / 100 * vehicle_capacities[ev_i]))


def test_optimise_simple():
    charger_rates = [50, 50, 50, 12, 1000]  # 5 Chargers; chargers 0, 1, 2, 3, 4
    scheduling_window_start = datetime(2021, 5, 21, hour=18)
    scheduling_window_end = datetime(2021, 5, 21, hour=19)
    scheduling_window_length = scheduling_window_end - scheduling_window_start
    num_ts = int(scheduling_window_length.total_seconds() / 60 / 15)

    timeslots = [TimeSlotInfo(date_time=scheduling_window_start + timedelta(minutes=ts_i*15), traditional_prod=50,
                              consumption=0, renewables_prod=0,
                              max_capacity=50, available_chargers=[i for i in range(5)],
                              existing_schedules=[]) for ts_i in range(num_ts)]  # 15:00 - 18:00
    # 17:00
    arrival = datetime(2021, 5, 21, hour=18, minute=0)
    departure = datetime(2021, 5, 21, hour=18, minute=21)
    vehicles = [VehicleInfo(ev_id=0, time_period=(arrival, departure), arrival_soc=0, soc_demand=100,
                            battery_capacity=1, charger_id=3),
                VehicleInfo(ev_id=1, time_period=(datetime(2021, 5, 21, hour=18), datetime(2021, 5, 21, hour=18,
                                                                                           minute=45)),
                            arrival_soc=0, soc_demand=100,
                            battery_capacity=500, charger_id=4)]

    scheduler = LPScheduler([], [], [], charger_rates=charger_rates, allocation_strategy=FirstChoiceAllocation())
    schedule = scheduler.schedule(vehicles, timeslots)

    print("\n",schedule.get_schedules())
    print(schedule.get_schedule_status())


def simulate_scheduler_client():
    # Example for one scheduling window
    start_day = 31
    start_month = 8
    start_year = 2021
    num_days = 1
    min_in_day = 1440
    ts_interval_length = 15
    num_ts = num_days * min_in_day // ts_interval_length
    num_evs = 50
    num_chargers = num_evs
    charger_rates = [7 for i in range(num_chargers)]
    dts = [datetime(start_year, start_month, start_day) + timedelta(minutes=15 * t) for t in range(num_ts)]

    # IMPORTANT: THE SCHEDULER KNOWS NOTHING ABOUT THESE SO THESE MUST BE UPDATED AS VEHICLES ARE SCHEDULED
    # (OR JUST KEPT TRACK OF IN SOME WAY, E.G. BY UPDATING THE CONTENTS OF TIME SLOT INFOS)
    charger_availability = [[c_id for c_id in range(num_chargers)] for ts_i in range(num_ts)]
    curr_timetable = [[] for ts_i in range(num_ts)]

    timeslots = [TimeSlotInfo(date_time=dts[ts_i], traditional_prod=80,
                              consumption=random.randint(30, 80), renewables_prod=random.randint(0, 20),
                              max_capacity=1000, available_chargers=[i for i in range(num_chargers)],
                              existing_schedules=[])
                 for ts_i in range(num_ts)]

    vehicle_socs = []
    vehicle_capacities = []
    vehicle_times = []
    vehicle_chargers = []
    for ev_i in range(num_evs):
        arrival_soc = random.randint(50, 70)
        departure_soc = random.randint(arrival_soc+10, 100)
        vehicle_socs.append([arrival_soc, departure_soc])
        vehicle_capacities.append(random.choice(BATTERY_CAPACITIES))
        vehicle_chargers.append(random.randint(0, num_chargers-1))

        required_charge = (departure_soc - arrival_soc) // 100 * vehicle_capacities[ev_i]
        charger_rate_limit = charger_rates[vehicle_chargers[ev_i]] // 4
        minimum_timeslots = required_charge // charger_rate_limit if required_charge >= charger_rate_limit else 1

        arrival = random.randint(0, (num_ts - 1) * 15 - 15 - minimum_timeslots * 15) \
            if (num_ts - 1) * 15 - 15 - minimum_timeslots * 15 >= 0 else random.randint(0, ((num_ts - 1) * 15 - 15))

        departure = random.randint(min(arrival + minimum_timeslots * 15, (num_ts - 1) * 15), (num_ts - 1) * 15)

        # Use as offsets for datetime arrival and departure
        da = timedelta(hours=(arrival // 60), minutes=(arrival / 60 % 1) * 60)
        dd = timedelta(hours=(departure // 60), minutes=(departure / 60 % 1) * 60)

        arrival = datetime(start_year, start_month, start_day) + da
        departure = datetime(start_year, start_month, start_day) + dd

        vehicle_times.append((arrival, departure))

    # Manually add some vehicles
    vehicles = [VehicleInfo(ev_id=ev_id, time_period=(vehicle_times[ev_id]), arrival_soc=vehicle_socs[ev_id][0],
                            soc_demand=vehicle_socs[ev_id][1], battery_capacity=vehicle_capacities[ev_id],
                            charger_id=vehicle_chargers[ev_id])
                for ev_id in range(num_evs)]
    # vehicles.append(VehicleInfo(ev_id=25, time_period=(datetime(start_year, start_month, 31, hour=23),
    #                                                   datetime(start_year, start_month+1, 1, hour=23)),
    #                             arrival_soc=10, soc_demand=100, battery_capacity=100, charger_id=2))
    # vehicles.append(VehicleInfo(ev_id=26, time_period=(datetime(start_year, start_month, 31, hour=23),
    #                                                   datetime(start_year, start_month+1, 1, hour=23)),
    #                             arrival_soc=10, soc_demand=100, battery_capacity=100, charger_id=2))

    scheduler = LPScheduler(["Traditional Producers"], ["Consumers"], ["Renewable Producers"], charger_rates,
                            interval_length=ts_interval_length, allocation_strategy=MostRenewablesAllocation())

    # Schedule vehicles sequentially
    scheduled = []
    for ev in vehicles:
        print("EV {} | Time {} | SOC {} -> {} | Battery Capacity {}".format(ev.id, ev.time_period, ev.arrival_soc,
                                                                            ev.soc_demand, ev.battery_capacity))
        s = scheduler.schedule([ev], timeslots)

        print("\n" + "-"*100 + "\n")
        print("Result: ", s.get_schedules())
        if ev.id not in s.get_schedules().keys():
            print("Failed to schedule EV {}. Scheduling status codes: {}".format(ev.id, s.get_schedule_status()))
            continue

        # Add existing vehicle schedule "slot" to the relevant time slots
        for ts_i in range(num_ts):
            print([ev.ev_id for ev in s.timetable[ts_i]])
            for schedule_info in s.timetable[ts_i]:
                if schedule_info.ev_id not in scheduled:
                    timeslots[ts_i].existing_schedules.append(schedule_info)

        scheduled.append(ev.id)
        print(scheduled)

        # Can also have a timetable that is updated
        # add_schedules_to_timetable(curr_timetable, s, scheduler, first_ts, timeslots)

        # Uncomment to print state of existing_vehicles for each time slot
        for ts_i in range(num_ts):
            print(" ".format(ts_i).center(3), end="| ")
            for si in timeslots[ts_i].existing_schedules:
                print(si.ev_id, end=" ")
            print()

        # Notice how with first choice allocation, there are lots of failed attempts because first choice does not
        # move the scheduling window around to find a suitable allocation of time slots
        for ts_i in range(num_ts):
            charge_sum = 0
            for si in timeslots[ts_i].existing_schedules:
                charge_sum += si.charge
            if timeslots[ts_i].renewables_prod + timeslots[ts_i].traditional_prod <= charge_sum + timeslots[
                ts_i].consumption:
                print("Consumption > Production at {}".format(ts_i))

    for ts_i in range(num_ts):
        charge_sum = 0
        for si in timeslots[ts_i].existing_schedules:
            charge_sum += si.charge
        print("Production at TS {}: {} | Consumption: {}".format(ts_i,
                                                                 timeslots[ts_i].renewables_prod
                                                                 + timeslots[ts_i].traditional_prod,
                                                                 charge_sum + timeslots[ts_i].consumption))

    # If an "outside" timetable is used to keep track of schedules, can print the schedules like so:
    # print_timetable(curr_timetable)


def add_schedules_to_timetable(timetable, schedules, scheduler, first_ts, timeslots):
    offset = scheduler.convert_datetime_to_minutes_with_offset(schedules.timetable_start, first_ts)
    schedule_timetable = schedules.timetable
    for ts_i in range(len(schedule_timetable)):
        for s in schedule_timetable[ts_i]:
            new_schedule = ScheduleInfo(ev_id=s.ev_id,
                                        charge=s.charge,
                                        charger_id=s.charger_id,
                                        arrival=s.arrival,
                                        departure=s.departure)
            timetable[offset + ts_i].append(new_schedule)
            timeslots[ts_i].existing_schedules.append(new_schedule)


def print_timetable(timetable):
    print("TS".ljust(4) + "|| ScheduleInfos (EV ID)".ljust(4))
    for ts_i in range(len(timetable)):
        print(str(ts_i).ljust(4), end="|| ")
        for s in timetable[ts_i]:
            print(str(s.ev_id).center(4), end="| ")
        print()


if __name__ == "__main__":
    random.seed(42)
    start_time = time.monotonic()
    # test_optimise_simple()
    test_optimise_random()
    # test_optimise()
    # simulate_scheduler_client()
    end_time = time.monotonic()
    print("\nRun time: ", timedelta(seconds=end_time - start_time))
