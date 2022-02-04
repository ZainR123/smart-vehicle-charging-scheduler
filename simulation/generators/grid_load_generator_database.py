import numpy as np
import random
import mysql.connector


class GridLoadGenerator:
    """Generator for grid load values by fetching data from a database.

    Attributes:
        _data: A numpy array of grid load values from a database.
        generated_data: A numpy array of generated predicted grid load values that are ready for use.
    """
    def __init__(self):
        self._data = self._read_database_values()
        self.generated_data = self._apply_deviation()

    def _read_database_values(self):
        """Fetches predicted load vaues from a database.
        
        Returns:
            A numpy array of grid load values from a database.
        """
        db = mysql.connector.connect(host="schedulerdb.cv1vtvg9bql2.eu-west-2.rds.amazonaws.com", user="admin",
                                     passwd="password", _database="Scheduler")

        cursor = db.cursor()

        cursor.execute("SELECT Predicted_Load FROM grid_load_weekday")

        results = cursor.fetchall()

        data = np.asarray(results)
        data = data.astype(float)
        data = np.squeeze(data.tolist())

        return np.around(data, decimals=2)

    def _apply_deviation(self):
        """Applies deviation to all values fetched from the database.

        Returns:
            A numpy array of processed predicted load values (ready for use).
        """
        rand_day = random.randint(1, 7)
        if rand_day >= 6:
            return np.add(self._data, random.randint(3, 6))
        else:
            return np.subtract(self._data, random.randint(-3, 3))
