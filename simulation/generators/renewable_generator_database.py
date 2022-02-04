import numpy as np
import random
import mysql.connector


class RenewableGenerator:
    """Generator for renewable electricity by fetching data from a database.

    Attributes:
        _data: A numpy array of renewable electricity values from a database.
        generated_data: A numpy array of generated renewable electricity values that are ready for use.
    """
    def __init__(self):
        self._data = self._read_database_values()
        self.generated_data = self.apply_deviation()

    def _read_database_values(self):
        db = mysql.connector.connect(host="schedulerdb.cv1vtvg9bql2.eu-west-2.rds.amazonaws.com", user="admin",
                                     passwd="password", database="Scheduler")

        cursor = db.cursor()

        cursor.execute("SELECT Solar_Generation_Percent FROM wind_solar_perc")

        results = cursor.fetchall()

        data = np.asarray(results)
        data = data.astype(float)
        data = np.squeeze(data.tolist())

        return data

    def apply_deviation(self):
        array_dev = np.add(self._data, random.uniform(-0.12, 0.15))
        array_dev_trunc = np.around(array_dev, 2)
        return array_dev_trunc
