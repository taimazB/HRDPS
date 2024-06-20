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


# def extractNC(item):
#     fieldName, CANADA, fNC = item[0], item[1], item[2]
#     lonMin = CANADA['lonMin'].unique()[0]
#     lonMax = CANADA['lonMax'].unique()[0]
#     latMin = CANADA['latMin'].unique()[0]
#     latMax = CANADA['latMax'].unique()[0]
#     #
#     devNull = os.system('mkdir -p HRDPS/%s/CA' % fieldName)
#     devNull = os.system('cdo sellonlatbox,%f,%f,%f,%f HRDPS/%s/%s HRDPS/%s/CA/%s' %
#                         (lonMin, lonMax, latMin, latMax, fieldName, fNC, fieldName, fNC))


def extractProvince(item):
    province, lonNC, latNC, var, fieldName, varMin, varMax, fieldStep = item
    devNull = os.system(f'mkdir -p nc/{fieldName}/images/{province}')
    #
    ##  EXTRACT CITIES
    Canada = pd.read_csv(f'scripts/Canada.csv')
    selectedCities = Canada[Canada['province']==province]
    df = {}
    df['datetime'] = datetimes(selectedCities['tz'].iloc[0], fieldName)
    for i,city in enumerate(selectedCities.iterrows()):
        lon = city[1]['lon']
        lat = city[1]['lat']
        iLon = np.argmin(np.abs(lonNC-lon))
        iLat = np.argmin(np.abs(latNC-lat))
        values = []
        for var_t in var:
            if(fieldName == 'TMP' or fieldName == 'WSPD' or fieldName == 'HUMIDEX'):
                values.append(round(var_t[iLat,iLon]))
            else:
                values.append(round(var_t[iLat,iLon],1))
        #
        df[f"city_{i+1}"] = values
    df = pd.DataFrame(data=df)
    df.to_csv(f'data/{province}_{fieldName}.csv',index=None)
    #
    with open(f'topos/geojson/{province}.geojson') as f:
        geojson_data = json.load(f)
    #
    boundary_polygon = shape(geojson_data['features'][0]['geometry'])
    lonMin, latMin, lonMax, latMax = boundary_polygon.bounds
    # lonMid = (lonMin+lonMax)/2
    # latMid = (latMin+latMax)/2
    # dLon = lonMax-lonMin
    # dLat = latMax-latMin
    # maxWidth = max(dLon,dLat)+2
    # lonMin = lonMid-maxWidth/2
    # lonMax = lonMid+maxWidth/2
    # latMin = latMid-maxWidth/2
    # latMax = latMid+maxWidth/2
    #
    # maxXdistance = distance.geodesic([latMin,lonMin],[latMin,lonMax]).km
    # maxYdistance = distance.geodesic([latMin,lonMin],[latMax,lonMin]).km
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
    # with open(f'data/tz_{row["shortName"]}.txt', 'w') as f:
    #     for dt in datetimesLocal:
    #         f.write(dt + '\n')


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
    var = nc.variables[fieldName][:]  # .data
    # missingValue = nc[fieldName].missing_value
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

    


# def processB(item):
#     [i, fNC, field, cities, allColors] = item
#     devNull = os.system('mkdir -p HRDPS/%s/CA/tiles' % field['name'])
#     devNull = os.system('mkdir -p HRDPS/%s/CA/values' % field['name'])
#     #
#     fileName = fNC.split('.')[0]
#     nc = Dataset("HRDPS/%s/CA/%s.nc" % (field['name'], fileName), 'r')
#     varName = fileName.split('_')[1]
#     dateTime = '_'.join(fileName.split('_')[2:])
#     var = nc.variables[varName][:].data
#     missingValue = nc[varName].missing_value
#     #
#     # latitude, longitude, depth
#     lonNC = nc.variables['longitude'][:].data
#     latNC = nc.variables['latitude'][:].data
#     lonNC[lonNC >= 180] -= 360
#     #
#     var[var == missingValue] = -9999
#     f = interpolate.interp2d(lonNC, latNC, var, kind='linear')
#     #
#     lonNew = np.arange(-62.235, -52, 0.04) # np.arange(lonNC[0], lonNC[-1], 0.04)
#     latNew = np.arange(45, 55.235, 0.04) # np.arange(latNC[0], latNC[-1], 0.04)
#     #
#     varNew = f(lonNew, latNew)
#     #
#     import json
#     from shapely.geometry import shape, Point
#     #
#     with open('topos/geojson/N.geojson') as f:
#         geojson_data = json.load(f)
#     #
#     # Extract the boundary polygon from the GeoJSON file
#     boundary_polygon = shape(geojson_data['features'][0]['geometry'])
#     #
#     # Create meshgrid of latitude and longitude coordinates
#     long_grid, lat_grid = np.meshgrid(lonNew, latNew)
#     #
#     try:
#         mask.any()
#     except:
#         # Create a mask based on whether each point falls within the boundary polygon
#         mask = np.array([boundary_polygon.contains(Point(lon, lat)) for lon, lat in zip(long_grid.ravel(), lat_grid.ravel())])
#     #
#     if (np.any(~np.isnan(varNew))):
#         varNewRounded = np.flipud(np.round(varNew, int(-math.log10(field['step']))))
#         varNewRounded[varNewRounded < field['stops'][0]] = np.nan
#         varNewRounded[varNewRounded > field['stops'][-1]] = field['stops'][-1]
#         mask = mask.reshape(varNewRounded.shape)  # Reshape mask to match temperatures array shape
#         varNewRounded[~mask] = np.nan
#         varNewInt = ((varNewRounded - field['stops'][0]) / field['step'])+1
#         varNewInt = 100*(varNewInt-np.nanmin(varNewInt))
#         varNewInt[np.isnan(varNewInt)] = 0
#         varNewInt = varNewInt.astype(np.uint16)
#         imageio.imwrite(f"HRDPS/{field['name']}/CA/bw/{fileName}.png", varNewInt)
#         varNewInt = ((varNewRounded - field['stops'][0]) / field['step'])+1
#         varNewInt[np.isnan(varNewInt)] = 0
#         varNewInt = varNewInt.astype(np.uint16)
#         varColored = allColors[varNewInt].astype(np.uint8)
#         imageio.imwrite(f"HRDPS/{field['name']}/CA/colored/{fileName}.png", varColored)
