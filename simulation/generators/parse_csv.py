import csv
from itertools import islice
from pathlib import Path

path_ren_ahead = str(
    Path().resolve().parent) + "\\simulation_files\\renewable_day_ahead.csv"  # B1440
path_ren_now = str(
    Path().resolve().parent) + "\\simulation_files\\renewable_now.csv"  # B1440
path_ahead = str(
    Path().resolve().parent) + "\\simulation_files\\aggr_gen_ahead.csv"  # B1430
path_current = str(
    Path().resolve().parent) + "\\simulation_files\\actual_gen_now.csv"  # B1430


# Contains BMRS data © Elexon Limited copyright and database right 2021.
# https://www.elexon.co.uk/operations-settlement/bsc-central-services/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/

# Renewables production aggregate day ahead/ current
class APIResultParser:
    """Parser for the generated csv files containing the generated data required for the simulation.

    Attributes:
        renewable_aggr_now: An array of aggregate renewable electricity values generated at the current time in the
                            form of triples.
        renewable_aggr_ahead: An array of predicted aggregate renewable electricity values generated for tomorrow in
                              the form of triples.
        quantity_array_now: An array of total traditional electricity generation at the current time.
        quantity_array48: An array of total traditional electricity generation for 48 hours ahead of the current time.
    """

    def __init__(self):
        self.renewable_aggr_now = self.renewable_parse_now()
        self.renewable_aggr_ahead, self.renewable48 = self.renewable_parse_ahead()
        self.quantity_array_now = self.traditional_gen_now()
        self.quantity_array48 = self.traditional_gen_parse_ahead()

    def renewable_parse_now(self):
        with open(path_ren_now, "r") as infile:
            reader = csv.reader(infile, delimiter=",")
            data_headers = next(islice(reader, 4, None))

            found_section = False
            header = None
            type_index = data_headers.index("Power System Resource  Type")
            process_index = data_headers.index("Process Type")
            sp_index = data_headers.index("Settlement Period")
            quantity_index = data_headers.index("Quantity")

            type_array = []
            sp_array = []
            process_type = []

            solar_array = []
            wind_onshore_array = []
            wind_offshore_array = []

            for row in reader:
                if row[0] != "<EOF>":
                    if row[process_index] == "Day Ahead":
                        if row[type_index] == "Solar":
                            quantity = float(row[quantity_index])
                            solar_array.append(quantity)
                            solar_array.append(quantity)
                        elif row[type_index] == "Wind Offshore":
                            quantity = float(row[quantity_index])
                            wind_offshore_array.append(quantity)
                            wind_offshore_array.append(quantity)
                        elif row[type_index] == "Wind Onshore":
                            quantity = float(row[quantity_index])
                            wind_onshore_array.append(quantity)
                            wind_onshore_array.append(quantity)
                else:
                    break

        a = solar_array
        b = wind_onshore_array
        c = wind_offshore_array

        renewable_aggr_now = [int(a) + int(b) + int(c) for a, b, c in
                              zip(a, b, c)]

        print("renewable aggr now: " + str(len(renewable_aggr_now)))
        renewable_aggr_now = renewable_aggr_now[::-1]
        print(renewable_aggr_now)

        return renewable_aggr_now

    def renewable_parse_ahead(self):
        with open(path_ren_ahead, "r") as infile:
            reader = csv.reader(infile, delimiter=",")
            data_headers = next(islice(reader, 4, None))

            found_section = False
            header = None
            # type_index = None
            type_index = data_headers.index("Power System Resource  Type")
            process_index = data_headers.index("Process Type")
            sp_index = data_headers.index("Settlement Period")
            quantity_index = data_headers.index("Quantity")
            # print(type_index)

            type_array = []
            sp_array = []
            process_type = []

            solar_array = []
            wind_onshore_array = []
            wind_offshore_array = []

            for row in reader:
                if row[0] != "<EOF>":
                    if row[process_index] == "Day Ahead":
                        if row[type_index] == "Solar":
                            quantity = float(row[quantity_index])
                            solar_array.append(quantity)
                            solar_array.append(quantity)
                        elif row[type_index] == "Wind Offshore":
                            quantity = float(row[quantity_index])
                            wind_offshore_array.append(quantity)
                            wind_offshore_array.append(quantity)
                        elif row[type_index] == "Wind Onshore":
                            quantity = float(row[quantity_index])
                            wind_onshore_array.append(quantity)
                            wind_onshore_array.append(quantity)
                else:
                    break

        a = solar_array
        b = wind_onshore_array
        c = wind_offshore_array

        renewable_aggr_ahead = [int(a) + int(b) + int(c) for a, b, c in
                                zip(a, b, c)]

        print("renewable aggr dayahead ", len(renewable_aggr_ahead))
        renewable_aggr_ahead = renewable_aggr_ahead[::-1]
        print(renewable_aggr_ahead)

        renewable48 = self.renewable_aggr_now + renewable_aggr_ahead  # 192 timelslot list renewables.
        renewable48div100 = [x / 100 for x in renewable48]

        print("renewable 48 hours: ", len(renewable48))
        print(renewable48)

        print("renewable 48 hours div 100: ", len(renewable48div100))
        print(renewable48div100)

        return renewable_aggr_ahead, renewable48

    def traditional_gen_now(self):
        ### ACTUAL GEN NOW B1620
        with open(path_current, "r") as infile:
            reader = csv.reader(infile, delimiter=",")
            data_headers = next(islice(reader, 4, None))

            found_section = False
            header = None
            quantity_index = data_headers.index("Quantity")
            # print(type_index)

            type_array = []
            sp_array = []
            quantity_array_now = []
            combined = []

            # for level, group in itertools.groupby(sorted_rows, key=sort_key):
            #     total = sum(int(col2sumgetter(row)) for row in group)
            #     print(level, total)
            # https: // stackoverflow.com / questions / 63420600 / how - can - calculate - the - sum - of - a - column - but - taking - specific - rows - of - it - in -python

            for row in reader:
                if row[0] != "<EOF>":
                    quantity = float(row[quantity_index])
                    quantity_array_now.append(quantity)
                    quantity_array_now.append(quantity)
                    # quantity_array_now.append(quantity)  # doubled for testing
                    # quantity_array_now.append(quantity)
                else:
                    break

        print("TOTAL GEN NOW :  " + str(len(quantity_array_now)))
        quantity_array_now = quantity_array_now[::-1]
        print(quantity_array_now)  # 192 timeslot traditional generation

        traditional_aggr = [quantity_array_now - self.renewable_aggr_now for
                            self.renewable_aggr_now, quantity_array_now
                            in
                            zip(self.renewable_aggr_now, quantity_array_now)]
        print("trad aggr now " + str(len(traditional_aggr)))
        print(traditional_aggr)

        return quantity_array_now  # 192 timeslot traditional generation

    def traditional_gen_parse_ahead(self):
        ### ACTUAL GEN NOW B1620
        with open(path_ahead, "r") as infile:
            reader = csv.reader(infile, delimiter=",")
            data_headers = next(islice(reader, 4, None))

            found_section = False
            header = None
            quantity_index = data_headers.index("Quantity")

            type_array = []
            sp_array = []
            quantity_array_ahead = []
            combined = []

            for row in reader:
                if row[0] != "<EOF>":
                    quantity = float(row[quantity_index])
                    quantity_array_ahead.append(quantity)
                    quantity_array_ahead.append(quantity)
                else:
                    break

        print("TOTAL gen ahead :  " + str(len(quantity_array_ahead)))
        quantity_array_ahead = quantity_array_ahead[::-1]
        print(quantity_array_ahead)

        traditional_aggr_ahead = [
            quantity_array_ahead - self.renewable_aggr_ahead for
            self.renewable_aggr_ahead, quantity_array_ahead in
            zip(self.renewable_aggr_ahead, quantity_array_ahead)]

        print("trad aggr ahead " + str(len(traditional_aggr_ahead)))
        print(traditional_aggr_ahead)

        traditional48 = traditional_aggr_ahead + self.quantity_array_now  # 192 timeslot 48 hour traditional generation
        traditional48div100 = [x / 100 for x in traditional48]

        print("traditional 48 hours : ", len(traditional48))
        print(traditional48)
        print("traditional 48 hours /100: ", len(traditional48div100))
        print(traditional48div100)

        return traditional48  # 192 timeslot traditional generation


APIResultParser()
# parse_api.__init__()
# # parse_api.renewable_parse()
# parse_api.traditional_gen_parse()
# # parse_api.renewable_parse_now()
