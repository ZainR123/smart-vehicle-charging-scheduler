"""Dummy LPScheduler class to serve as placeholder.
"""

from scheduler.lp_scheduler import ScheduleInfo


class Timetable:
    def __init__(self, initial_datetime, timetable):
        self.initial_datetime = initial_datetime  # NOTE: CURRENTLY IN FORMAT (DAY, TIME (MINUTES))
        self.timetable = timetable

    def get_schedules(self):
        return {0: {"arrival_day": 23, "arrival_time": 0, "departure_day": 23, "departure_time": 15}}


class LPScheduler:
    """Dummy LPScheduler class for testing purposes. Returns a manually defined timetable.
    """

    def __init__(self, producers, consumers, renewables_producers, charger_rates, allocation_strategy=None):
        self.producers = producers
        self.consumers = consumers
        self.charger_rates = charger_rates
        self.renewables_producers = renewables_producers

    def schedule(self, vehicles, timeslots):
        charge_schedule = [[ScheduleInfo(ev_id=0,
                                         charge=0,
                                         charger_id=0,
                                         arrival=(23, 0),
                                         departure=(23, 15))]
                           for ts in timeslots]

        return Timetable((0, 0), charge_schedule)


if __name__ == "__main__":
    # How to use:
    #
    # from simulation.scheduler.lp_scheduler_dummy import LPScheduler
    #
    # scheduler = LPScheduler([], [], [], [])
    # schedule = scheduler.schedule([], [])
    #
    # Inputs don't matter at all for dummy, but they can be passed to it. Returns static sample schedule.

    # Scheduler output:
    scheduler = LPScheduler([], [], [], [])  # Takes the producers, consumers, renewables_producers and charger_rates
    schedule = scheduler.schedule([], [])  # Takes a list of VehicleInfo and list of TimeSlotInfo

    # For schedule only
    print(schedule.get_schedules())
    print("Vehicle 0 arrives at day", schedule.get_schedules()[0]["arrival_day"])  # How to access day/time specifically

    # For internal timetable contents
    for ts_i in range(len(schedule.timetable)):
        print("Time slot", ts_i, end=" || ")
        for s in schedule.timetable[ts_i]:
            print("Vehicle {}, Charge for {} kWh, Using Charger {}, Arriving at day {} at {}th minute, Departing at "
                  "day {} at {}th minute."
                  .format(s.ev_id, s.charge, s.charger_id, s.arrival[0], s.arrival[1], s.departure[0], s.departure[1]))
