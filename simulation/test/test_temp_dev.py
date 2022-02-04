"""File used temporarily for testing and developing the initial algorithms
for the cumulative first come first serve scheduler.

Temporarily used for testing the cumulative FCFS algorithm independently from other subsystems of the
offline scheduler.
"""
from scheduler.scheduling import TimeSlot, ChargingPoint, Vehicle
from scheduler.cumulative_fcfs_scheduler import CumulativeFCFSScheduler
from generators.grid_load_generator import GridLoadGenerator
from generators.renewable_generator import RenewableGenerator
from random import randint
from datetime import timedelta


def convert_time_range(t):
    time_range = str(timedelta(minutes=t))[:-3]
    if "1 day" in time_range:
        return "00:00"
    else:
        return time_range


def print_table(schedule_timetable):  # Print timetable in a table format
    timetable = [[None for chargeslot in range(NUM_OF_CHARGE_POINTS)] for timeslot in range(len(schedule_timetable))]

    for timeslot in range(len(schedule_timetable)):
        i = 0
        for ev in schedule_timetable[timeslot]:
            timetable[timeslot][i] = ev
            i += 1

    print("Time slot".center(15) + "|", end="")
    for slot in range(NUM_OF_CHARGE_POINTS):
        print(("SLOT " + str(slot)).center(8) + "|", end="")
    print()

    for i in range(len(timetable)):
        print((convert_time_range(i * 15) + " - " + convert_time_range(i * 15 + 15)).center(14), "|", end="")
        for ev in timetable[i]:
            if ev:
                print(("EV " + str(ev.id)).center(8) + "|", end="")
            else:
                print(" ".center(8) + "|", end="")
        print()


def generate_predicted_load():
    load_gen = GridLoadGenerator()

    return load_gen.generated_data


def generate_predicted_renewable():
    renewable_gen = RenewableGenerator()

    return renewable_gen.generated_data


if __name__ == "__main__":
    # First, setup charging points, vehicles and empty list of time slots
    NUM_OF_CHARGE_POINTS = 2

    # As the charges are not being used for scheduling right now, they are set to 0 here but in practice, the charges
    # would likely be set and used by the simulation in some way. Furthermore, most criteria other than the availability
    # and the load currently have very little effect as the scheduler prioritises the former two criteria. Of the two,
    # the scheduler prioritises availability more, so there may be situations where a vehicle is scheduled into a time
    # slot even if the grid load at that time slot would exceed the maximum load capacity. This should be reflected in
    # the visualisation.

    # Vehicles are scheduled in order, with the first to be scheduled as vehicle 0
    # vehicles = []

    # for index in range(len(userInput.evID)):
    #    vehicle = Vehicle(userInput.evID[index], userInput.arrivalTime[index], userInput.chargeDuration[index],
    #                      userInput.waitTime[index], userInput.currentCharge[index], userInput.capacityArray[index], userInput.prefTime[index])
    #    vehicles.append(vehicle)

    vehicles = [
        # Suppose that vehicle 0 arrives at around 7:00 and wants to charge for 70 minutes. The vehicle
        # does not need charging right away, so its acceptable wait time is 65 minutes.
        Vehicle(0, 420, 70, 65, 0, 500, 10),
        # Suppose that vehicle 1 arrives at around 8:20 and wants to charge for 20 minutes. The vehicle does
        # not need charging right away, so its acceptable wait time is 30 minutes.
        Vehicle(1, 500, 20, 30, 0, 400, 5),
        # Suppose that vehicle 2 arrives at around the same time as vehicle 0 and wants to charge for 30
        # minutes. This should put vehicle 2 at the same time slots as vehicle 0 if there are free time slots.
        Vehicle(2, 422, 30, 50, 0, 450, 6),
        # Suppose that vehicle 3 arrives with (hypothetically) the exactly the same parameters as vehicle 2.
        # If there are no time slots left, vehicle 3 should be staggered into later time slots that are free.
        Vehicle(3, 422, 30, 50, 0, 650, 8),
        Vehicle(4, 420, 70, 0, 0, 700, 8),
        Vehicle(5, 420, 70, 0, 0, 700, 6),
        Vehicle(6, 420, 70, 0, 0, 400, 4),
        # Vehicle 7 only wants to charge for 20 minutes...
        # See how the staggering can yield undesirable results...
        Vehicle(7, 420, 20, 0, 0, 300, 1)
    ]

    # Other set of vehicles to test
    # vehicles = [Vehicle(0, 720, 10, 30, 0),
    #             Vehicle(1, 500, 20, 30, 0),
    #             Vehicle(2, 0, 30, 50, 0),
    #             Vehicle(3, 720, 150, 30, 0),
    #             Vehicle(4, 720, 60, 30, 0),
    #             Vehicle(5, 720, 60, 30, 0),
    #             Vehicle(6, 720, 60, 30, 0),
    #             Vehicle(7, 720, 60, 30, 0),
    #             # Vehicle 8 wants to charge for approx 4.02 hours from 20:00, but this will not be possible because
    #             # the current scheduler only schedules for one day and the requested duration of charge exceeds the
    #             # day by 1 minute.
    #             Vehicle(8, 1200, 241, 30, 0),
    #             # When scheduling vehicle 9, something goes wrong and its arrival time is invalid. In this case,
    #             # the scheduler will also not schedule vehicle 9
    #             Vehicle(9, 1441, 60, 30, 0)
    # ]

    charge_points = [ChargingPoint() for i in range(NUM_OF_CHARGE_POINTS)]
    timeslots = []

    # Then setup sample data for each timeslot
    avg_max_load = 120

    # First generate list of predicted load values
    predicted_load_list = generate_predicted_load()

    # Now we can obtain the highest load for the day
    highest_load = max([load for load in predicted_load_list])

    # Then generate energy percentages
    generation_mix_list = generate_predicted_renewable()

    # Then create the time slots data; we use test_index to loop through each list of data
    test_index = 0
    for time in range(0, 1440, 15):
        generation_mix = generation_mix_list[test_index]
        predicted_load = predicted_load_list[test_index]

        # I just generate the max load values immediately here since there's no need to track it
        max_load = highest_load + randint(5, 10)
        timeslots.append(TimeSlot(time, generation_mix, max_load, predicted_load, highest_load))
        test_index += 1

    # Create the FCFS scheduler and schedule all Vehicle objects in vehicles list
    print("Scheduling vehicles...")
    schedules = []
    scheduler = CumulativeFCFSScheduler(charge_points=charge_points)
    for vehicle in vehicles:
        schedule_temp = scheduler.schedule(vehicle, timeslots)
        if schedule_temp:
            schedules = schedule_temp
        else:
            print("It is not possible to schedule vehicle " + str(vehicle.id))

    # Print the timetable
    print("-" * 20 + "\nDone!\n")
    print_table(schedules)
