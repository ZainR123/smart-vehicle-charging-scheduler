from datetime import datetime, timedelta

import mysql.connector
from dateutil.relativedelta import relativedelta

from scheduler.lp_scheduler import LPScheduler, VehicleInfo, TimeSlotInfo, \
    ScheduleInfo

from generators.simple_api_request import BMRSAPIRequest
from generators.parse_csv import APIResultParser
from generators.local_consumption_generator import ConsumptionTariffGenerator

db = mysql.connector.connect(
    host="schedulerdb.cv1vtvg9bql2.eu-west-2.rds.amazonaws.com", user="admin",
    passwd="password", database="Scheduler")
cursor = db.cursor()

newStart = datetime.now()
newEnd = datetime.now()
isClashing = 0
clashed = False

while 1:

    db.commit()
    cursor.execute("SELECT id FROM userdata WHERE Is_Scheduling = 1 limit 1")
    results = cursor.fetchall()
    row_count = cursor.rowcount

    if row_count != 0:

        cursor.execute(
            "SELECT id FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()
        evID = results[0]
        evID = int(''.join(map(str, evID)))

        cursor.execute(
            "SELECT Current_Charge FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()
        currentCharge = results[0]
        currentCharge = int(''.join(map(str, currentCharge)))

        cursor.execute(
            "SELECT Preferred_Start_Datetime FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()
        prefStart = results[0]
        prefStart = str(''.join(map(str, prefStart)))

        cursor.execute(
            "SELECT Preferred_End_Datetime FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()
        prefEnd = results[0]
        prefEnd = str(''.join(map(str, prefEnd)))

        cursor.execute(
            "SELECT Preferred_Charge_Level FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()
        prefCharge = results[0]
        prefCharge = int(''.join(map(str, prefCharge)))

        cursor.execute(
            "SELECT Preferred_Charge_Station FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()
        prefStation = results[0]
        prefStation = int(''.join(map(str, prefStation)))

        cursor.execute(
            "SELECT Car FROM userdata WHERE Is_Scheduling = 1 ORDER BY Arrival limit 1")
        results = cursor.fetchall()

        car = results[0]

        cursor.execute(
            "SELECT Battery_Capacity FROM cardata WHERE Car_Model = %s", car)
        results = cursor.fetchall()
        batteryCap = results[0]
        batteryCap = int(''.join(map(str, batteryCap)))

        scheduler = LPScheduler(["producers"], ["consumers"],
                                ["renewable producers"], [50, 50])

        prefStart = datetime.strptime(prefStart, '%Y-%m-%d %H:%M:%S')
        prefEnd = datetime.strptime(prefEnd, '%Y-%m-%d %H:%M:%S')

        if isClashing != 0:
            prefStart = newStart
            prefEnd = newEnd

        prefEnd = prefEnd + relativedelta(minutes=15)

        duration = prefEnd - prefStart
        minutes = duration.total_seconds() / 60
        numOfTimeslots = int(
            LPScheduler.discretise_time(scheduler, minutes) / 15)

        timeslotList = []

        BMRSAPIRequest()

        tweakedStation = prefStation

        if tweakedStation == 2:
            tweakedStation = 0

        parser = APIResultParser()
        parser2 = ConsumptionTariffGenerator()
        renewable_production = parser.renewable48
        consumption = parser2.data_array
        traditional_production = parser.quantity_array_now

        for i in range(numOfTimeslots):

            scheduleInfoList = []
            start = prefStart + timedelta(minutes=15 * i)

            db.commit()
            sql25 = "SELECT idEV FROM userTimes WHERE Timeslots = %s AND idEV <> %s"
            adr25 = (start, evID)
            cursor.execute(sql25, adr25)
            results = cursor.fetchall()
            row_count1 = cursor.rowcount

            if row_count1 != 0:

                sql20 = "SELECT idEV FROM userTimes WHERE Timeslots = %s AND idEV <> %s"
                adr20 = (start, evID)
                cursor.execute(sql20, adr20)
                results1 = cursor.fetchall()
                idList = list(results1)

                sql21 = "SELECT chargeInSlot FROM userTimes WHERE Timeslots = %s AND idEV <> %s"
                adr21 = (start, evID)
                cursor.execute(sql21, adr21)
                results2 = cursor.fetchall()

                sql22 = "SELECT chargerID FROM userTimes WHERE Timeslots = %s AND idEV <> %s"
                adr22 = (start, evID)
                cursor.execute(sql22, adr22)
                results3 = cursor.fetchall()

                sql23 = "SELECT ArrivalTime FROM userTimes WHERE Timeslots = %s AND idEV <> %s"
                adr23 = (start, evID)
                cursor.execute(sql23, adr23)
                results4 = cursor.fetchall()

                sql24 = "SELECT EndTime FROM userTimes WHERE Timeslots = %s AND idEV <> %s"
                adr24 = (start, evID)
                cursor.execute(sql24, adr24)
                results5 = cursor.fetchall()

                for x in range(len(idList)):
                    station = int(''.join(map(str, results3[x])))

                    if station == 2:
                        station = 0

                    scheduleInfoList.append(
                        ScheduleInfo(ev_id=int(''.join(map(str, results1[x]))),
                                     charge=int(''.join(map(str, results2[x]))),
                                     charger_id=station,
                                     arrival=datetime.strptime(
                                         str(''.join(map(str, results4[x]))),
                                         '%Y-%m-%d %H:%M:%S'),
                                     departure=datetime.strptime(
                                         str(''.join(map(str, results5[x]))),
                                         '%Y-%m-%d %H:%M:%S')))
                timeslotList.append(
                    TimeSlotInfo(
                        date_time=prefStart + timedelta(minutes=15 * i),
                        traditional_prod=traditional_production[i],
                        consumption=consumption[i],
                        renewables_prod=renewable_production[i],
                        max_capacity=1000,
                        available_chargers=[tweakedStation],
                        existing_schedules=scheduleInfoList))

            else:
                timeslotList.append(
                    TimeSlotInfo(
                        date_time=prefStart + timedelta(minutes=15 * i),
                        traditional_prod=traditional_production[i],
                        consumption=consumption[i],
                        renewables_prod=renewable_production[i],
                        max_capacity=1000,
                        available_chargers=[tweakedStation],
                        existing_schedules=None))

        s = scheduler.schedule(
            [VehicleInfo(ev_id=evID, time_period=(prefStart, prefEnd),
                         arrival_soc=currentCharge, soc_demand=prefCharge,
                         battery_capacity=batteryCap,
                         charger_id=tweakedStation)], timeslotList)
        if evID not in s.get_schedules().keys():
            sql6 = "UPDATE userdata SET Error = %s WHERE id = %s"
            adr6 = ("1", evID)
            cursor.execute(sql6, adr6)
            sql11 = "UPDATE userdata SET Is_Scheduling = %s WHERE id = %s"
            adr11 = ("0", evID)
            cursor.execute(sql11, adr11)

        else:

            startCharge = s.get_schedules()[evID]["arrival"]
            endCharge = s.get_schedules()[evID]["departure"]
            finalCharge = s.get_schedules()[evID]["charge"]
            finalCharge = (finalCharge / batteryCap) * 100

            sql = "SELECT Scheduled_Datetime_End FROM userdata WHERE Scheduled_Datetime_Start < %s AND Scheduled_Datetime_End > %s AND Charging_Station = %s AND id <> %s"
            adr = (endCharge, startCharge, prefStation, evID)
            cursor.execute(sql, adr)
            results = cursor.fetchall()
            isClashing = cursor.rowcount

            if isClashing != 0:
                end = results[0]
                end = str(''.join(map(str, end)))
                end = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                diff = endCharge - startCharge
                minutes = diff.total_seconds() / 60
                newStart = end
                newEnd = end + timedelta(minutes=minutes)
                clashed = True

            if not clashed:
                for i in range(numOfTimeslots):
                    start = prefStart + timedelta(minutes=15 * i)
                    sql100 = "DELETE FROM userTimes WHERE Timeslots = %s"
                    adr100 = (start,)
                    cursor.execute(sql100, adr100)
                    db.commit()

                sql101 = "DELETE FROM userTimes WHERE idEV = %s"
                adr101 = (evID,)
                cursor.execute(sql101, adr101)
                db.commit()

                currentTime = s.timetable_start
                for timeslot in s.timetable:
                    for scheduleInfo in timeslot:
                        sql16 = "INSERT INTO userTimes(idEV, chargeInSlot, Timeslots, ArrivalTime, EndTime, chargerID) VALUES (%s, %s, %s, %s, %s, %s) "
                        adr16 = (
                            scheduleInfo.ev_id, scheduleInfo.charge,
                            currentTime,
                            scheduleInfo.arrival, scheduleInfo.departure,
                            (-scheduleInfo.charger_id) + 1)
                        cursor.execute(sql16, adr16)
                        db.commit()

                    currentTime = currentTime + relativedelta(minutes=15)

                sql6 = "UPDATE userdata SET Scheduled_Datetime_Start = %s WHERE id = %s"
                adr6 = (startCharge, evID)
                cursor.execute(sql6, adr6)
                sql7 = "UPDATE userdata SET Scheduled_Datetime_End = %s WHERE id = %s"
                adr7 = (endCharge, evID)
                cursor.execute(sql7, adr7)
                sql8 = "UPDATE userdata SET Charging_Station = %s WHERE id = %s"
                adr8 = (prefStation, evID)
                cursor.execute(sql8, adr8)
                sql9 = "UPDATE userdata SET Final_Charge = %s WHERE id = %s"
                adr9 = (finalCharge, evID)
                cursor.execute(sql9, adr9)
                sql11 = "UPDATE userdata SET Is_Scheduling = %s WHERE id = %s"
                adr11 = ("0", evID)
                cursor.execute(sql11, adr11)

            elif isClashing == 0 and clashed:

                sql4 = "UPDATE userdata SET New_Sugg_Start = %s WHERE id = %s"
                adr4 = (startCharge, evID)
                cursor.execute(sql4, adr4)
                sql5 = "UPDATE userdata SET New_Sugg_End = %s WHERE id = %s"
                adr5 = (endCharge, evID)
                cursor.execute(sql5, adr5)
                sql10 = "UPDATE userdata SET Is_Scheduling = %s WHERE id = %s"
                adr10 = ("0", evID)
                cursor.execute(sql10, adr10)
                sql3 = "UPDATE userdata SET Slot_Taken = %s WHERE id = %s"
                adr3 = ("1", evID)
                cursor.execute(sql3, adr3)
                clashed = 0

            db.commit()
