import numpy as np
from netCDF4 import Dataset
# import matplotlib.pyplot as plt
from scipy import interpolate
import multiprocessing
import os
import imageio
import math
from PIL import ImageColor
from datetime import datetime, timedelta
from glob import glob
import pandas as pd
import itertools
import pytz
from PIL import Image, ImageDraw, ImageFont
import json
from shapely.geometry import shape, Point
from geopy import distance
from pathlib import Path


def colorRange(color1, color2, n):
    colors = []
    for r, g, b, a in zip(np.linspace(color1[0], color2[0], n),
                          np.linspace(color1[1], color2[1], n),
                          np.linspace(color1[2], color2[2], n),
                          np.linspace(color1[3], color2[3], n)):
        colors.append((r, g, b, a))
    return colors


def genColors(stops, colors, step):
    allColors = np.array([[0, 0, 0, 255]])
    for i in np.arange(len(stops) - 1):
        minStop = float(stops[i])
        minColor = colors[i]
        maxStop = float(stops[i + 1])
        maxColor = colors[i + 1]
        n = round((maxStop - minStop) / step)
        #
        newColors = np.array(
            colorRange(ImageColor.getcolor(minColor, 'RGBA'),
                       ImageColor.getcolor(maxColor, 'RGBA'), n))
        if (len(newColors) > 0):
            allColors = np.concatenate((allColors, newColors), axis=0)

    lastColor = list(ImageColor.getcolor(colors[-1], 'RGBA'))
    allColors = np.concatenate((allColors, [lastColor]), axis=0)
    return allColors


def extractProvince(item):
    province, lonNC, latNC, var, fieldName, varMin, varMax, fieldStep = item
    devNull = os.system(f'mkdir -p nc/{fieldName}/images/{province}')
    #
    ##  EXTRACT CITIES
    cities = pd.read_csv(f'scripts/cities.csv')
    selectedCities = cities[cities['province']==province]
    df = {}
    df['datetime'] = datetimes(selectedCities['tz'].iloc[0], fieldName)
    for row in selectedCities.iterrows():
        id = row[1]['id']
        lon = row[1]['lon']
        lat = row[1]['lat']
        iLon = np.argmin(np.abs(lonNC-lon))
        iLat = np.argmin(np.abs(latNC-lat))
        values = []
        for var_t in var:
            values.append(var_t[iLat,iLon])
        df[f"city_{id}"] = values
    #
    df = pd.DataFrame(data=df)
    df.to_csv(f'data/{province}_{fieldName}.csv',index=None)
    #
    with open(f'topos/geojson/{province}.geojson') as f:
        geojson_data = json.load(f)
    #
    boundary_polygon = shape(geojson_data['features'][0]['geometry'])
    lonMin, latMin, lonMax, latMax = boundary_polygon.bounds
    #
    iLonMin = np.argmin(np.abs(lonNC-lonMin))
    iLonMax = np.argmin(np.abs(lonNC-lonMax))
    iLatMin = np.argmin(np.abs(latNC-latMin))
    iLatMax = np.argmin(np.abs(latNC-latMax))
    #
    lonSub = lonNC[iLonMin:iLonMax+1]
    latSub = latNC[iLatMin:iLatMax+1]
    varSub = var[:, iLatMin:iLatMax+1, iLonMin:iLonMax+1]
    #
    lonGrid, latGrid = np.meshgrid(lonSub, latSub)
    mask = np.array([boundary_polygon.contains(Point(lon, lat))
                    for lon, lat in zip(lonGrid.ravel(), latGrid.ravel())])
    mask = mask.reshape(varSub[0, :, :].shape)
    #
    offset = 0.1
    maxPixelValue = 2**16-1
    for i, varStep in enumerate(varSub):
        varStep = varStep.data
        varStep += offset # TO PRESERVE PROVINCE BOUNDARIES FOR FIELDS LIKE RAIN AND SNOW
        varStep[varStep < varMin] = varMin
        varStep[varStep > varMax] = varMax
        varStep[~mask] = np.nan
        varNewInt = maxPixelValue*(varStep - varMin) / (varMax - varMin)
        varNewInt[np.isnan(varNewInt)] = 0
        varNewInt = varNewInt.astype(np.uint16)
        output = f"nc/{fieldName}/images/{province}/f{'%03d' % (i+1)}.png"
        imageio.imwrite(output, np.flipud(varNewInt))


def datetimes(timeZone, fieldName):
    files = sorted(glob(f'nc/{fieldName}/HRDPS*.nc'))
    datetimes = ['_'.join(Path(f).stem.split('_')[2:]) for f in files]
    #
    utc = pytz.utc
    #
    tz = pytz.timezone(timeZone)
    datetimesLocal = [datetime.strptime(dt, '%Y%m%d_%H').replace(tzinfo=utc).astimezone(tz).strftime('%A, %B %d-%H:%M') for dt in datetimes]
    return datetimesLocal


def process(field):
    fieldName = field['name'].iloc[0]
    stops = field['stops'].iloc[0]
    colors = field['colors'].iloc[0]
    step = field['step'].iloc[0]
    #
    devNull = os.system(f'cdo -O merge nc/{fieldName}/HRDPS*.nc nc/{fieldName}/all.nc')
    devNull = os.system(f'mkdir -p nc/{fieldName}/images')
    #
    nc = Dataset(f"nc/{fieldName}/all.nc")
    var = nc.variables[fieldName][:]
    #
    # latitude, longitude
    lonNC = nc.variables['longitude'][:].data
    latNC = nc.variables['latitude'][:].data
    #
    # var[var == missingValue] = -9999
    # varMin = np.nanmin(var)
    varMin = stops[0]
    varMax = stops[-1]
    #
    # 32: Max number of colors in a Blender color_ramp
    #T allColors = genColors(stops, colors, step)
    #T iSelectedColors = np.round(np.linspace(
    #T     0, len(allColors)-1, 32)).astype(np.uint16)
    #T colorStops = np.linspace(0.1/(varMax-varMin),1,32)
    #T np.savetxt(f'data/colors_{fieldName}', np.c_[colorStops, allColors[iSelectedColors]/255])
    #
    listExtract = []
    for province in ['N', 'L', 'NS', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC']:
        listExtract.append([province, lonNC, latNC, var,
                           fieldName, varMin, varMax, step])
    #
    with multiprocessing.Pool() as p:
        p.map(extractProvince, listExtract)
