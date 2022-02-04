from datetime import datetime, timedelta
from pathlib import Path

import requests


# Contains BMRS data © Elexon Limited copyright and database right 2021.
# https://www.elexon.co.uk/operations-settlement/bsc-central-services/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/


class BMRSAPIRequest:

    def __init__(self):
        self.request_actual_gen()
        self.request_day_ahead_total()
        self.request_day_ahead_renewables()
        self.request_renewables_now()

    """Request data using the BMRS API."""

    @staticmethod
    def request_actual_gen():
        """Performs an HTTP request to obtain data on actual electricity generated at the current time and writes the
        fetched data to a csv file.
        """
        settlement_date = "SettlementDate=" + datetime.today().strftime(
            "%Y-%m-%d")

        url = 'https://api.bmreports.com/BMRS/B1430/v1?APIKey=5nm8pho28jrdhdc&{}&Period=*&ServiceType=csv'.format(
            settlement_date)

        print(url)
        r = requests.get(url)

        path = str(
            Path().resolve().parent) + "\\simulation_files\\actual_gen_now.csv"

        with open(path, 'wb') as f:
            f.write(r.content)

    @staticmethod
    def request_day_ahead_total():
        """Performs an HTTP request to obtain data on day ahead total electricity generation predictions and writes the
        fetched data to a csv file.
        """
        settlement_date = "SettlementDate=" + (
                    datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        url = 'https://api.bmreports.com/BMRS/B1430/v1?APIKey=5nm8pho28jrdhdc&{}&Period=*&ServiceType=csv'.format(
            settlement_date)

        print(url)
        r = requests.get(url)

        path = str(
            Path().resolve().parent) + "\\simulation_files\\aggr_gen_ahead.csv"

        with open(path, 'wb') as f:
            f.write(r.content)

    @staticmethod
    def request_day_ahead_renewables():
        """Performs an HTTP request to obtain data on day ahead renewable electricity generation predictions and writes
        the fetched data to a csv file.
        """
        settlement_date = "SettlementDate=" + datetime.today().strftime(
            "%Y-%m-%d")

        url = 'https://api.bmreports.com/BMRS/B1440/v1?APIKey=5nm8pho28jrdhdc&{}&Period=*&ServiceType=csv'.format(
            settlement_date)

        print(url)
        r = requests.get(url)

        path = str(
            Path().resolve().parent) + "\\simulation_files\\renewable_day_ahead.csv"

        with open(path, 'wb') as f:
            f.write(r.content)

    @staticmethod
    def request_renewables_now():
        """Performs an HTTP request to obtain data on renewable electricity generation at the current time
        and writes the fetched data to a csv file.
        """
        settlement_date = "SettlementDate=" + (
                    datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

        url = 'https://api.bmreports.com/BMRS/B1440/v1?APIKey=5nm8pho28jrdhdc&{}&Period=*&ServiceType=csv'.format(
            settlement_date)

        print(url)
        r = requests.get(url)

        path = str(
            Path().resolve().parent) + "\\simulation_files\\renewable_now.csv"

        with open(path, 'wb') as f:
            f.write(r.content)
