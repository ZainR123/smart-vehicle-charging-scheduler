from pathlib import Path

import numpy as np

from generators.grid_load_generator import GridLoadGenerator
from charging_station.unscheduled import ChargingStation
from graphing.plot_graph import OutputGraph
from charging_station.scheduled import UChargingStation


class OutputCSV:

    def __init__(self):
        self.predicted_load_list = self.generate_predicted_load()
        self.placeholder_load = self.generate_predicted_load()
        self.array_zip = self.zip_arrays()
        self.writeCSV()
        OutputGraph()

    @staticmethod
    def generate_predicted_load():
        load_gen = GridLoadGenerator()
        return load_gen.generated_data

    def zip_arrays(self):
        a = np.arange(1, 97)
        b = UChargingStation.maxload
        c = UChargingStation.scheduledcars
        d = ChargingStation.timeslots
        return np.array(list(zip(a, b, c, d)))

    def writeCSV(self):
        path = str(Path().resolve().parent) + "\\simulation_files\\myout.csv"
        with open(path, 'w') as f:
            header = "Timeslot,Predicted_load_MW,fcfs_load,std_load\n"  # predicted load actually refers
            # to max capacity
            f.write(header)
            np.savetxt(f, self.array_zip, delimiter=',', fmt='%1.2f')


write_csv = OutputCSV()
write_csv.__init__()
