from datetime import datetime, timedelta, date

import requests


class CarbonIntensityAPIRequest:
    """Request data using the Carbon Intensity API."""

    def request(self):
        """Performs an HTTP request to the Carbon Intensity website to obtain electricity generation percentages.

        Returns:
            A dictionary of generation mix percentages in the format:
            {"carbon": carbon_array,
             "biomass": biomass_array,
             "coal": coal_array,
             "imports": imports_array,
             "gas": gas_array,
             "nuclear": nuclear_array,
             "other": other_array,
             "hydro": hydro_array,
             "solar": solar_array,
             "wind": wind_array}
        """
        now = datetime.now()
        time = now.strftime("%H:%M")
        start_date = date.today()
        end_date = start_date + timedelta(days=1)

        headers = {
            'Accept': 'application/json'
        }

        intensity = requests.get('https://api.carbonintensity.org.uk/regional/intensity/{0}T{1}Z/fw24h/postcode/NG8'.format(start_date, time), headers=headers)
        intensity = intensity.json()

        carbon_array = []
        biomass_array = []
        coal_array = []
        imports_array = []
        gas_array = []
        nuclear_array = []
        other_array = []
        hydro_array = []
        solar_array = []
        wind_array = []

        data = intensity.get('data')
        data = data.get('data')

        for x in data:
            carbon_intensity = x['intensity']
            carbon = carbon_intensity['forecast']
            gen_mix = x['generationmix']

            bio = gen_mix[0]
            bio_perc = bio['perc']
            coal = gen_mix[1]
            coal_perc = coal['perc']
            imports = gen_mix[2]
            imports_perc = imports['perc']
            gas = gen_mix[3]
            gas_perc = gas['perc']
            nuclear = gen_mix[4]
            nuclear_perc = nuclear['perc']
            other = gen_mix[5]
            other_perc = other['perc']
            hydro = gen_mix[6]
            hydro_perc = hydro['perc']
            solar = gen_mix[7]
            solar_perc = solar['perc']
            wind = gen_mix[8]
            wind_perc = wind['perc']

            carbon_array.append(carbon)
            biomass_array.append(bio_perc)
            coal_array.append(coal_perc)
            imports_array.append(imports_perc)
            gas_array.append(gas_perc)
            nuclear_array.append(nuclear_perc)
            other_array.append(other_perc)
            hydro_array.append(hydro_perc)
            solar_array.append(solar_perc)
            wind_array.append(wind_perc)

        return {"carbon": carbon_array,
                "biomass": biomass_array,
                "coal": coal_array,
                "imports": imports_array,
                "gas": gas_array,
                "nuclear": nuclear_array,
                "other": other_array,
                "hydro": hydro_array,
                "solar": solar_array,
                "wind": wind_array}
