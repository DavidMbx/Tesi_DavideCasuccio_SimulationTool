# -*- coding: utf-8 -*-
"""
    pvprediction.weather
    ~~~~~
    
    This module provides functions to read :class:`pvprediction.Weather` objects, 
    used as reference to calculate a photovoltaic installations' generated power.
    The provided environmental data contains temperatures and horizontal 
    solar irradiation, which can be used, to calculate the effective irradiance 
    on defined, tilted photovoltaic systems.
    
"""
import logging
logger = logging.getLogger('pvprediction.weather')

import os
import glob
import eccodes
#import pygrib
import math
import numpy as np
import pandas as pd
import pvlib as pv
import datetime
import csv


def forecast(date, timezone, longitude=None, latitude=None, var=None, method='DWD_CSV'):
    """ 
    Reads the predicted weather data for a specified location, retrieved through 
    several possible methods:
    
    
    - DWD_GRIB2:
        Reads an hourly interval of 23 hours from available forecast files, provided by
        the DWDs' (Deutscher Wetterdienst) Global Data Set ftp server, where a new data set 
        of the following 23 hours gets provided every 6 hours in GRIB2 format.
        The directory with available GRIB2 files has to be specified with the 'var' parameter.
    
    - DWD_CSV:
        Reads an hourly interval of 23 hours from a csv file, parsed from data provided by
        the DWDs' (Deutscher Wetterdienst) Global Data Set ftp server, where a new data set 
        of the following 23 hours gets provided every 6 hours in GRIB2 format.
        The csv directory has to be specified with the 'var' parameter.
    
    
    :param date: 
        the date for which the closest possible weather forecast will be looked up for.
        For many applications, passing datetime.datetime.now() will suffice.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    :param longitude: 
        the locations degree north of the equator in decimal degrees notation.
    :type longitude:
        float
    
    :param latitude: 
        the locations degree east of the prime meridian in decimal degrees notation.
    :type latitude:
        float
    
    :param method: 
        the defining method, how the weather data should be retrieved.
    :type method:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' and 'temperature', indexed by 
        timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvprediction.Weather`
    """
    if method.lower() == 'dwd_grib2':
        return _read_dwd(date, timezone, longitude, latitude, var)
    elif method.lower() == 'dwd_csv':
        csv = _get_dwdcsv_nearest(date, var)
        return _read_dwdcsv(csv, timezone)
    else:
        raise ValueError('Invalid irradiation forecast method "{}"'.method)


def reference(date, timezone, var=None, method='DWD_PUB'):
    """ 
    Reads historical weather data for a specified location, retrieved through 
    several possible methods:
    
    - DWD_PUB:
        Reads an hourly interval of 23 hours from a text file, provided by the DWDs' 
        (Deutscher Wetterdienst) public ftp server, where data will be updated roughly
        once a month.
        The DWD specific location key has to be specified with the 'var' parameter.
    
    
    :param date: 
        the date for which the closest possible weather forecast will be looked up for.
        For many applications, passing datetime.datetime.now() will suffice.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    :param method: 
        the defining method, how the weather data should be retrieved.
    :type method:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvprediction.Weather`
    """
    if method.lower() == 'dwd_pub':
        return _read_dwdpublic(var, timezone)
    else:
        raise ValueError('Invalid irradiation reference method "{}"'.method)


def _read_dwd(date, timezone, longitude, latitude, path):
    """
    Reads an hourly interval of 23 hours from available forecast files, provided by
    the DWDs' (Deutscher Wetterdienst) Global Data Set ftp server, where a new data set 
    of the following 23 hours gets provided every 6 hours in GRIB2 format.
    
    
    :param date: 
        the date for which the latest available forecast will be looked up for.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone: 
        str or unicode
    
    :param longitude: 
        the locations degree north of the equator in decimal degrees notation.
    :type longitude:
        float
    
    :param latitude: 
        the locations degree east of the prime meridian in decimal degrees notation.
    :type latitude:
        float
    
    :param path: 
        the directory in which a directory "dwd", containing compressed GRIB2 files, should be looked for.
    :type path: 
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvprediction.Weather`
    """
    
    # initialize variables    
    dwdpath = os.path.join(os.path.join(path, "dwd"))
    fields = ["aswdifd_s", "aswdir_s", "t_2m", "t_g"]
    
    lastForecast = None
    for f in range(len(fields)):
        # get date of latest forecast
        dirList = os.listdir(os.path.join(dwdpath, fields[f]))
        dirList.sort(reverse = True)
        if dirList[0].rsplit("_", 2)[0] == 120:
            lastForecast = dirList[0].rsplit("_", 2)[1]
    
    if lastForecast != None:
        # unpack compressed, latest forecast
        os.system("bunzip2 --keep `find " + dwdpath + " -name '*" + lastForecast + "*.bz2'`")
        
        dates = []
        data = []
        for f in range(len(fields)):
            # list all extracted grib files
            dirList = glob.glob(os.path.join(dwdpath, fields[f], "*" + lastForecast + "*.grib2"))
            dirList.sort()
    
            lastValue = 0
            data.append([])
            
            if len(dirList) >= 48:
                for i in range(24):
                    grb = pygrib.open(dirList[i])
                    grb.seek(0)
                    
                    lat, lon = grb.latlons()
                    i, j = _get_location_nearest(lat, lon, latitude, longitude)
                    
                    lastTimestamp = False
                    firstTimestamp = False
                    for g in grb:
                        timestamp = datetime.datetime.strptime(str(g['validityDate']) + " " + '%0.0f'%(g['validityTime']/100.0), "%Y%m%d %H")
                        
                        if lastTimestamp:
                            if f == 0:
                                datestr = datetime.datetime.strftime(lastTimestamp, "%Y-%m-%d %H")
                                dates.append(datestr)
                            
                            if fields[f] == "aswdifd_s" or fields[f] == "aswdir_s":
                                diff = (timestamp - lastTimestamp).total_seconds() / 3600.0
                                value = (1 / diff) * ((timestamp - firstTimestamp).total_seconds() / 3600 * g['values'][i, j] - (lastTimestamp - firstTimestamp).total_seconds() / 3600 * lastValue)
                            else:
                                value = g['values'][i, j]
                            
                            data[f].append(value)
                            
                        else:
                            firstTimestamp = timestamp
                        
                        lastTimestamp = timestamp
                        lastValue = g['values'][i, j]
                        
                    grb.close()
        
        if len(dates) > 0:
            csvpath = os.path.join(os.path.join(path, "csv"))
            with open(os.path.join(csvpath, "DWD_" + lastForecast + ".csv"), 'wb') as csvfile:
                writer = csv.writer(csvfile, delimiter = ",")
                line = ["time"]
                line.extend(fields)
                writer.writerow(line)
                for i in range(len(dates)):
                    line = [dates[i] + ":00:00"]
                    for j in range(len(fields)):
                        line.append(data[j][i])
                    writer.writerow(line)
        
        # clean up
        os.system("find " + dwdpath + " -name '*" + lastForecast + "*.grib2' -exec rm -f {} \;")
    
    return None;

def _get_location_nearest(lat1, long1, lat2, long2):

    # Code taken from
    # http://www.johndcook.com/blog/python_longitude_latitude/ This
    # code (FUNCTION) is in the public domain. Do whatever you want
    # with it, no strings attached according to website.
    
    # Convert latitude and longitude to 
    # spherical coordinates in radians.
    
    degrees_to_radians = np.pi/180.0
         
    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians
         
    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
         
    # Compute spherical distance from spherical coordinates.
         
    # For two locations in spherical coordinates 
    # (1, theta, phi) and (1, theta, phi)
    # cosine( arc length ) = 
    #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
     
    cos = (np.sin(phi1)*np.sin(phi2)*np.cos(theta1 - theta2) + 
           np.cos(phi1)*np.cos(phi2))
    arc = np.arccos( cos )
 
    # Remember to multiply arc by the radius of the earth 
    # in your favorite set of units to get length.
    return arc

def _read_dwdcsv(csvname, timezone):
    """
    Reads an hourly interval of 23 hours from a csv file, parsed from data provided by
    the DWDs' (Deutscher Wetterdienst) Global Data Set ftp server, where a new data set 
    of the following 23 hours gets provided every 6 hours in GRIB2 format.
    
    
    :param csvname: 
        the name of the csv file, containing the weather data.
    :type csvname:
        str or unicode
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvprediction.Weather`
    """
    csv = pd.read_csv(csvname, 
                      usecols=['time','aswdifd_s','aswdir_s','t_2m','t_g'], 
                      index_col='time', parse_dates=['time'])
        
    csv = csv.ix[:,:'t_2m'].rename(columns = {'aswdir_s':'direct_horizontal', 'aswdifd_s':'diffuse_horizontal', 't_2m':'temperature'})
    csv.index.name = 'time'
    
    if not csv.empty:
        csv.index = csv.index.tz_localize('UTC').tz_convert(timezone)
        
        csv = np.absolute(csv)
        
        # Convert the ambient temperature from Kelvin to Celsius
        csv['temperature'] = csv['temperature'] - 273.15
    
    result = Weather(csv)
    result.key = os.path.basename(csvname).replace('.csv', '')
    return result


def _get_dwdcsv_nearest(date, path):
    """
    Retrieve the csv file closest to a passed date, following the file naming
    scheme "KEY_YYYYMMDDHH.csv"
    
    
    :param date: 
        the date for which the closest possible csv file will be looked up for.
    :type date: 
        :class:`pandas.tslib.Timestamp` or datetime
    
    :param path: 
        the directory in which a directory "csv", containing the converted csv files, should be looked for.
    :type path:
        str or unicode
    
    
    :returns: 
        the full path and filename of the closest found csv file.
    :rtype: 
        str
    """

    cswdir = os.path.dirname(path)
    print('dir' + cswdir)
    dwdkey = os.path.basename(path)
    print(dwdkey)

    #    if isinstance(date, pd.tslib.Timestamp):
 #       date = date.tz_convert('UTC')
    
    ref = int(date.strftime('%Y%m%d%H'))
    diff = 1970010100
    csv = None
    try:
        for f in os.listdir(cswdir):
            if dwdkey + '_' in f and not '_yield' in f and f.endswith('.csv'):
                d = abs(ref - int(f[3:-4]))
                if (d < diff):
                    diff = d
                    csv = f
    except IOError:
        logger.error('Unable to read irradiance forecast file in "%s"', path)
    else:
        if(csv == None):
            raise IOError('Unable to find irradiance forecast files in "%s"', path)
        else:
            return os.path.join(path, csv)


def _read_dwdpublic(key, timezone):
    """
    Reads an hourly interval of 23 hours from a text file, provided by the DWDs' 
    (Deutscher Wetterdienst) public ftp server, where data will be updated roughly
    once a month.
    
    
    :param key: 
        the DWD specific location key. Information about possible locations can be found with:
        ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/solar/ST_Beschreibung_Stationen.txt
    :type key:
        str or unicode
    
    :param timezone: 
        See http://en.wikipedia.org/wiki/List_of_tz_database_time_zones for a list of 
        valid time zones.
    :type timezone:
        str or unicode
    
    
    :returns: 
        the Weather object, containing the data columns 'global_horizontal' or 
        'direct_horizontal', 'diffuse_horizontal' in W/m^2 and 'temperature' in 
        degree Celsius, indexed by timezone aware :class:`pandas.DatetimeIndex`.
    :rtype: 
        :class:`pvprediction.Weather`
    """
    from urllib import urlopen
    from zipfile import ZipFile
    from StringIO import StringIO
    
    # Retrieve measured temperature values from DWD public ftp server
    url = urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/air_temperature/recent/stundenwerte_TU_' + key + '_akt.zip')
    zipfile = ZipFile(StringIO(url.read()))
    for f in zipfile.namelist():
        if ('produkt_temp_Terminwerte_' in f):
            temp = pd.read_csv(zipfile.open(f), sep=";",
                                        usecols=[' MESS_DATUM',' LUFTTEMPERATUR'])
    temp.index = pd.to_datetime(temp[' MESS_DATUM'], format="%Y%m%d%H")
    temp.index = temp.index.tz_localize('UTC').tz_convert(timezone)
    temp.index.name = 'time'
    temp = temp.rename(columns = {' LUFTTEMPERATUR':'temperature'})
    
    # Missing values get identified with "-999"
    temp = temp.replace('-999', np.nan)
    
    
    # Retrieve measured solar irradiation observations from DWD public ftp server
    url = urlopen('ftp://ftp-cdc.dwd.de/pub/CDC/observations_germany/climate/hourly/solar/stundenwerte_ST_' + key + '.zip')
    zipfile = ZipFile(StringIO(url.read()))
    for f in zipfile.namelist():
        if ('produkt_strahlung_Stundenwerte_' in f):
            irr = pd.read_csv(zipfile.open(f), sep=";",
                                        usecols=[' MESS_DATUM','DIFFUS_HIMMEL_KW_J','GLOBAL_KW_J'])
    
    irr.index = pd.to_datetime(irr[' MESS_DATUM'], format="%Y%m%d%H:%M")
    irr.index = irr.index.tz_localize('UTC').tz_convert(timezone)
    irr.index.name = 'time'
    
    # Shift index by 30 min, to move from interval center values to hourly averages
    irr.index = irr.index - datetime.timedelta(minutes=30)
    
    # Missing values get identified with "-999"
    irr = irr.replace('-999', np.nan)
    
    # Global and diffuse irradiation unit transformation from hourly J/cm^2 to mean W/m^2
    irr['global_horizontal'] = irr['GLOBAL_KW_J']*(100**2)/3600
    irr['diffuse_horizontal'] = irr['DIFFUS_HIMMEL_KW_J']*(100**2)/3600
    
    reference = pd.concat([irr['global_horizontal'], irr['diffuse_horizontal'], temp['temperature']], axis=1)
    # Drop rows without either solar irradiation or temperature values
    reference = reference[(reference.index >= temp.index[0]) & (reference.index >= irr.index[0]) & 
                          (reference.index <= temp.index[-1]) & (reference.index <= irr.index[-1])]
    
    result = Weather(reference)
    result.key = key
    return result

    
class Weather(pd.DataFrame):
    """
    The Weather object provides horizontal solar irradiation and temperature
    data as a :class:`pandas.DataFrame`. It needs to contain specific columns, 
    to being able to calculate the total solar irradiation on a defined photovoltaic
    systems' tilted surface.
    
    A Weather DataFrame contains either the columns 'global_horizontal' or 
    'direct_horizontal', additional to 'diffuse_horizontal' and 'temperature'.
    Depending on which columns are available, :func:`calculate` will calculate
    the total irradiance on the passed photovoltaic systems' tilted surface in a 
    slightly adjusted matter.
    """
    _metadata = ['key']
 
    @property
    def _constructor(self):
        return Weather
    
    
    def calculate(self, system):
        """ 
        Calculates the total solar irradiation on a defined photovoltaic systems' 
        tilted surface, consisting out of the sum of direct, diffuse and reflected 
        irradiance components.
        
        :param system: 
            the photovoltaic system, defining the surface orientation and tilt to 
            calculate the irradiance for.
        :type system: 
            :class:`pvprediction.System`
        """
        timestamps = pd.date_range(self.index[0], self.index[-1] + pd.DateOffset(minutes=59), freq='min').tz_convert('UTC')
        pressure = pv.atmosphere.alt2pres(system.location.altitude)
        
        dhi = self.diffuse_horizontal.resample('1min', kind='timestamp').last().ffill()
        dhi.index = dhi.index.tz_convert('UTC')
            
        if 'global_horizontal' in self.columns:
            ghi = self.global_horizontal.resample('1min', kind='timestamp').last().ffill()
        else:
            ghi = self.direct_horizontal.resample('1min', kind='timestamp').last().ffill() + dhi
        ghi.index = ghi.index.tz_convert('UTC')
        
        # Get the solar angles, determining the suns irradiation on a surface by an implementation of the NREL SPA algorithm
        angles = pv.solarposition.get_solarposition(timestamps, system.location.latitude, system.location.longitude, altitude=system.location.altitude, pressure=pressure)
        
        if 'global_horizontal' in self.columns:
            zenith = angles['apparent_zenith'].copy()
            zenith[angles['apparent_zenith'] > 87] = np.NaN
            zenith = zenith.dropna(axis=0)
            dni = pv.irradiance.dirint(ghi[zenith.index], zenith, zenith.index, pressure=pressure)
            dni = pd.Series(dni, index=timestamps).fillna(0)
        else:
            # Determine direct normal irradiance as defined by Quaschning
            dni = ((ghi - dhi)*(1/np.sin(np.deg2rad(angles['elevation'])))).fillna(0)
            dni.loc[dni <= 0] = 0
        
        # Determine extraterrestrial radiation and airmass
        extra = pv.irradiance.get_extra_radiation(timestamps)
        airmass_rel = pv.atmosphere.get_relative_airmass(angles['apparent_zenith'])
        airmass = pv.atmosphere.get_absolute_airmass(airmass_rel, pressure)
        
        # Calculate the total irradiation, using the perez model
        irradiation = pv.irradiance.get_total_irradiance(system.modules_param['tilt'], system.modules_param['azimuth'],
                                                angles['apparent_zenith'], angles['azimuth'],
                                                dni, ghi, dhi,
                                              dni_extra=extra, airmass=airmass,                                                albedo=system.modules_param['albedo'],
                                               model='perez')
        
#         direct = pv.irradiance.beam_component(system.modules_param['tilt'], system.modules_param['azimuth'], 
#                                               angles['zenith'], angles['azimuth'], 
#                                               dni)
#         
#         diffuse = pv.irradiance.perez(surface_tilt=system.modules_param['tilt'], surface_azimuth=system.modules_param['azimuth'], 
#                                       solar_zenith=angles['apparent_zenith'], solar_azimuth=angles['azimuth'], 
#                                       dhi=dhi, dni=dni, dni_extra=extra, 
#                                       airmass=airmass)
#          
#         reflected = pv.irradiance.grounddiffuse(surface_tilt=system.modules_param['tilt'], 
#                                                 ghi=ghi, 
#                                                 albedo=system.modules_param['albedo'])
        
        # Calculate total irradiation and replace values smaller than specific threshold
        # Check if still necessary, for better forecasts
        total = irradiation['poa_global'].fillna(0)
#         total = direct.fillna(0) + diffuse.fillna(0) + reflected.fillna(0)
        total_hourly = total.resample('1h').mean()
        total_hourly.loc[total_hourly < 0.01] = 0
        total_hourly.index = total_hourly.index.tz_convert(system.location.tz)
        
        return pd.Series(total_hourly, name='irradiation')
