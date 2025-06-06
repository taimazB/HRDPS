import numpy as np
from netCDF4 import Dataset
from glob import glob
import os
from scipy import interpolate
from multiprocessing import Pool
import pandas as pd
import csv
import sys


variable = sys.argv[1]
method = sys.argv[2]

files = sorted(glob('%s/*.nc' % variable))
file = files[0]
nc = Dataset(file, 'r')
latitude = nc.variables['latitude'][:].data
longitude = nc.variables['longitude'][:].data

##  READ AND INTERPOLATE NC FILES
def read(file):
    fileName = os.path.splitext(os.path.basename(file))[0]
    dateTime = '_'.join(fileName.split('_')[2:])
    nc = Dataset(file, 'r')
    values = nc.variables[variable][:].data
    return(dateTime, interpolate.RegularGridInterpolator((latitude, longitude), values, method=method, bounds_error=False, fill_value=-999))

with Pool() as p:
    interps = p.map(read, files)


##  EXTRACT VALUES AT STATIONS COORDINATES
def extractStationsDateTimes(row):
    ID = row[1]
    lat = row[2]
    lon = row[3]
    array = []
    for interp in interps:
        dateTime = interp[0]
        value = interp[1]([lat,lon])[0]
        array.append([ID, lat, lon, dateTime, round(value,1)])
    #
    # with open('%s/stations/%s.csv' % (variable, ID), 'w') as f:
    #     write = csv.writer(f)
    #     write.writerow(['dateTime','value'])
    #     write.writerows(data)
    return array

def saveStations(df):
    os.makedirs('%s/stations' % variable)
    stationIDs = df.ID.unique()
    for stationID in stationIDs:
        df[df.ID==stationID].to_csv('%s/stations/%s.csv' % (variable, stationID), index=False, columns=['dateTime', 'value'])

def saveDateTimes(df):
    os.makedirs('%s/dateTimes' % variable)
    dateTimes = df.dateTime.unique()
    for dateTime in dateTimes:
        df[df.dateTime==dateTime].to_csv('%s/dateTimes/%s.csv' % (variable, dateTime), index=False, columns=['ID', 'lat', 'lon', 'value'])

stations = pd.read_csv('../scripts/stations.csv')

with Pool() as p:
    data = p.map(extractStationsDateTimes, list(stations.itertuples(name=None)))
    data = np.array(data)
    data = data.reshape(-1,5)
    df = pd.DataFrame(data, columns=['ID','lat','lon','dateTime','value'])
    #
    saveStations(df)
    saveDateTimes(df)
    #
    dateTimes = df.dateTime.unique()