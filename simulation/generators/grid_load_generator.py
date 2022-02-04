import csv
import numpy as np
import random

from pathlib import Path


class GridLoadGenerator:
    """DEPRECATED. Generator for grid load data by loading a csv a file of values and applying deviation values to 
    them.
    
    Attributes:
        _data_array: A numpy array of predicted grid load (demand) values.
        generated_data: A numpy array of data values that have been processed for use.
    """
    def __init__(self):
        self._data_array = self._read_file_values()
        self.generated_data = self.apply_deviation()

    def _read_file_values(self):
        path = str(Path().resolve().parent) + "\\simulation_files\\grid_load_weekday.csv"

        with open(path, newline="") as file:
            reader = csv.reader(file)
            next(reader)
            data = [row[1] for row in reader]
            _data_array = np.asarray(data)
            _data_array = _data_array.astype(float)

        return np.around(_data_array, decimals=2)

    def apply_deviation(self):
        rand_day = random.randint(1, 7)
        if rand_day >= 6:
            return np.add(self._data_array, random.randint(3, 6))
        else:
            return np.subtract(self._data_array, random.randint(-3, 3))
