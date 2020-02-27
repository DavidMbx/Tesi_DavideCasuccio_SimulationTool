import cdsapi
import os

gen_dir = os.path.dirname(os.path.realpath('__file__'))
c = cdsapi.Client()

c.retrieve(
    'reanalysis-era5-land',
    {
        'area': '47/9/47/9',  # North, West, South, East. Default: global
         # Latitude/longitude grid: east-west (longitude) and north-south resolution (latitude). Default: 0.25 x 0.25

        'variable': [
            '2m_temperature', 'soil_temperature_level_1',
            'surface_net_solar_radiation', 'surface_solar_radiation_downwards',
        ],
        'year': ['2015'],
        'month': [
            '10',
        ],
        'day': [
            '11',


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
    os.path.join(gen_dir,"../GRIB_files/download.grib"))
