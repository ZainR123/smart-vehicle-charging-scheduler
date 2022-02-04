import csv
import numpy as np
import random

from pathlib import Path


class ConsumptionTariffGenerator:
    """Generator for price tariff values by fetching and processing data from files.

    Attributes:
        data_array: A numpy array of consumption values read from a file.
        generated_data: A numpy array of generated predicted grid load values that are ready for use.
    """
    def __init__(self):
        self.data_array = self._read_consumption_values()
        self.tariff_array = self._read_tariff_values()

        # self.generated_data = self.apply_deviation()

    def _read_consumption_values(self):
        """Reads consumption values from a file.

        Returns:
            An array of consumption values.
        """
        path = str(Path().resolve().parent) + "\\simulation_files\\household_consumption.csv"
        data_array = []

        with open(path, newline="") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[1] != "" and "<EOF>":
                    data_array.append(float(row[1]))
                    data_array.append(float(row[1]))
        print(len(data_array))
        print("data list", data_array)
        return data_array

    def _read_tariff_values(self):
        """Reads price tariff values from a file.

        Returns:
            An array of price tariff values.
        """
        # PRICE TARIFFS DETERMINED BY ON/OFF PEAK, WITH STATIC PRICE FOR EITHER WITHIN CERTAIN HOURS
        # 9PM - 7AM OFF PEAK
        path = str(Path().resolve().parent) + "\\simulation_files\\ev_energy_tariffs.csv"
        tariff_array = []

        with open(path, newline="") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[1] != "" and "<EOF>":
                    tariff_array.append(float(row[1]))
        print(len(tariff_array))
        print("PRICE TARIFF", tariff_array)
        return tariff_array
    # def apply_deviation(self):
    #     rand_day = random.randint(1, 7)
    #     if rand_day >= 6:
    #         return np.add(self.data_array, random.randint(3, 6))
    #     else:
    #         return np.subtract(self.data_array, random.randint(-3, 3))


ConsumptionTariffGenerator()
