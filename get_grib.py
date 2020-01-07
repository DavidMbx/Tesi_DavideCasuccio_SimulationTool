#!/usr/bin/env python
import cdsapi

c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-land',
    {
        'area': '41/14/41/14',  # North, West, South, East. Default: global
        'grid': [1.0, 1.0],
    # Latitude/longitude grid: east-west (longitude) and north-south resolution (latitude). Default: 0.25 x 0.25

        'variable': [
            '2m_temperature', 'forecast_albedo', 'soil_temperature_level_1',
            'surface_net_solar_radiation', 'surface_solar_radiation_downwards',
        ],
        'year': '2019',
        'month': [
            '01', '07',
        ],
        'day': [
            '01'
        ],
        'time': [
            '00:00', '01:00', '02:00',
            '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00',
            '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00',
            '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00',
            '21:00', '22:00', '23:00',
        ],
        'format': 'grib',
    },
    'download.grib')
