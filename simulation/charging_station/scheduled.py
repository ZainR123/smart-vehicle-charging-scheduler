import random
import simpy

from scheduler.scheduling import TimeSlot, ChargingPoint, Vehicle
from scheduler.cumulative_fcfs_scheduler import CumulativeFCFSScheduler
from generators.grid_load_generator import GridLoadGenerator
from generators.renewable_generator import RenewableGenerator


class UChargingStation:

    def __init__(self):
        self.scheduledcars = scheduledcars
        self.maxload = max_load_list

    """diff between CharginStation.car and UChargingStation.car ???
    how does it interact with Vehicle if at all ?"""
    def car(env, timetable, scheduledload):

            #print('This is max load list before timetable', UChargingStation.maxload)
            print('In car')

            """ timetable? / 22 / 44 ??"""
            for n in range(len(timetable)):

                if len(timetable[n]) == 1:
                    scheduledload[n] = scheduledload[n] + 22

                if len(timetable[n]) == 2:
                    scheduledload[n] = scheduledload[n] + 44

            #print('This is max load list before assignment', UChargingStation.maxload)
            UChargingStation.scheduledcars = scheduledload

            """why 45 and 50?? """
            for n in range(len(scheduledcars)):
                max_load_list[n] = max_load_list[n] + random.randint(45, 50)
            UChargingStation.maxload = max_load_list
            yield env.timeout(1)


    def simCars(env):

        charge_points = [ChargingPoint() for i in range(2)]
        timeslots = []
        predicted_load_list = gridloads.generated_data
        highest_load = max([load for load in predicted_load_list])
        generation_mix_list = renewables.generated_data

        test_index = 0
        for time in range(0, 1440, 15):
            generation_mix = generation_mix_list[test_index]
            predicted_load = predicted_load_list[test_index]

            # I just generate the max load values immediately here since there's no need to track it
            max_load = highest_load + random.randint(5, 10)
            timeslots.append(TimeSlot(time, generation_mix, max_load, predicted_load, highest_load))
            test_index += 1
        print('This is max load list before ', max_load_list)

        print('This is max load list after', max_load_list)


        schedules = []
        scheduler = CumulativeFCFSScheduler(charge_points=charge_points)
        for vehicle in vehicles:
            # TimeTableClass = scheduler.schedule(VehicleInfolist, TimeSlotlist)
            # for loop number of time slots
            #   for loop
            # TimeTableClass.timetable( TimeslotIndex,   )
            #
            schedule_temp = scheduler.schedule(vehicle, timeslots)
            if schedule_temp:
                schedules = schedule_temp

            else:
                print("It is not possible to schedule vehicle " + str(vehicle.id))

        print('This is the predicted load list before process: ', scheduledcars)

        env.process(UChargingStation.car(env, schedules, scheduledcars))




env = simpy.Environment()
bcs = simpy.Resource(env, capacity=2)

scheduler = CumulativeFCFSScheduler(charge_points=2)
gridloads = GridLoadGenerator()
gridloadvals = GridLoadGenerator()
renewables = RenewableGenerator()
scheduledcars = gridloads.generated_data
max_load_list = gridloadvals.generated_data

vehicles = [Vehicle(0, 420, 70, 65, 0, 10, None),
            Vehicle(1, 500, 20, 30, 0, 10, None),
            Vehicle(2, 422, 30, 50, 0, 10, None),
            Vehicle(3, 422, 30, 50, 0, 10, None),
            Vehicle(4, 420, 70, 0, 0, 10, None),
            Vehicle(5, 420, 70, 0, 0, 10, None),
            Vehicle(6, 420, 70, 0, 0, 10, None),
            Vehicle(7, 420, 20, 0, 0, 10, None)]




UChargingStation()
UChargingStation.simCars(env)

env.run(until=96)

print('This is scheduled cars after process: ', UChargingStation.scheduledcars)
print('This is max load list at end', UChargingStation.maxload)