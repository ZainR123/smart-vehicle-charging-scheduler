import math
import random
import simpy
from generators.grid_load_generator import GridLoadGenerator
from scheduler.lp_scheduler import VehicleInfo


# class Vehicle:
#     def __init__(self, id, arrival, duration, wait_time, charge):
#         self.id = id
#         self.arrival = arrival
#         self.duration = duration
#         self.wait_time = wait_time
#         self.charge = charge

"""Vehicle class, Changed parameters to follow new lpscheduler VehicleInfo params."""
class Vehicle:
    def __init__(self, id, time_period, arrival_soc, soc_demand, battery_capacity, charger_id):
        self.id = id
        self.time_period = time_period
        self.arrival_soc = arrival_soc
        self.soc_demand = soc_demand
        self.battery_capacity = battery_capacity
        self.charger_id = charger_id


"""Charging Station Class"""
class ChargingStation:

    """TODO: change parameters to follow lpscheduler (timeslots was old scheduler) ????"""
    def __init__(self, timeslots):
        self.timeslots = timeslots


    """how does car interact with vehicle?"""
    def car(env, name, bcs, driving_time, current_charge, battery_capacity):
        yield env.timeout(driving_time)
        print(env.now)
        timeslots[env.now] = '%s arriving' % name
        # print(timeslots)

        # if env.now % 4 == 0:
        print('%s arriving at %d:00' % (name, (env.now / 4)))
        arrival_time = env.now
        # else:
        #  print('%s arriving at %d:30' % (name, (env.now/4)))

        """????"""
        with bcs.request() as req:
            yield req

            print('%s starting to charge at %.2f with %s%% charge and a %skWh Battery' % (name, env.now / 4, current_charge, battery_capacity))
            chargetimeremaining = (((100 - current_charge) / 100) * battery_capacity) / 22
            print('%s will take approximately %.1f hours to charge to 100%%' % (name, chargetimeremaining))
            yield env.timeout(chargetimeremaining * 4)
            print('%s leaving the charging point at %.2f' % (name, env.now / 4))
            timeslots[math.floor(env.now)] = '%s leaving' % name
            print(env.now)
            print(timeslots)
            vehicles.append(Vehicle(name, arrival_time * 15, chargetimeremaining * 60, 0, current_charge))
            pointer = math.ceil(env.now) - arrival_time

            """22??"""
            for n in range(pointer):
                timeslotsload[arrival_time + n] = timeslotsload[arrival_time + n] + 22

            # print(timeslotsload)

        """TODO:"""
        ChargingStation.timeslots = timeslotsload

    """calls the above car method for a number of cars ??"""
    def simCars(env):
        for i in range(8):
            env.process(ChargingStation.car(env, 'Car %d' % (i + 1), bcs, random.randint(0, 96), random.randint(10, 40), random.randint(1, 3) * 20))


env = simpy.Environment()
bcs = simpy.Resource(env, capacity=2) #what is resource and why capacity 2?

gridloads = GridLoadGenerator()
timeslots = [0] * 96
timeslotsload = gridloads.generated_data
vehicles = []
n = 0


def convertTime(environmentTime):
    decimalTime = environmentTime / 4
    math.floor(decimalTime)


ChargingStation(timeslotsload)
ChargingStation.simCars(env)

env.run(until=96)

print(ChargingStation.timeslots)
