import csv
import numpy as np
import random

from pathlib import Path


class RenewableGenerator:
    """DEPRECATED. Generator for renewable electricity by loading a csv a file of values and applying deviation
    values to them.

    Attributes:
        _data_array: A numpy array of predicted renewable electricity generation values.
        generated_data: A numpy array of data values that have been processed for use.
    """
    def __init__(self):
        self._data_array = self._read_file_values()
        self.generated_data = self.apply_deviation()

    def _read_file_values(self):
        path = str(Path().resolve().parent) + "\\simulation_files\\Generators_win_solar_perc.csv"

        with open(path, newline="") as file:
            reader = csv.reader(file)
            next(reader)
            data = [row[1] for row in reader]
            data_array = np.asarray(data)
            data_array = data_array.astype(float)
        return data_array

    def apply_deviation(self):
        array_dev = np.add(self._data_array, random.uniform(-0.12, 0.15))
        array_dev_trunc = np.around(array_dev, 2)
        return array_dev_trunc
