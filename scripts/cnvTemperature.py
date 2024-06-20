import numpy as np
from netCDF4 import Dataset
import sys
import matplotlib.pyplot as plt
from scipy import interpolate
import multiprocessing
import os
import imageio
# import tracemalloc
from datetime import datetime, timedelta
import math


field = 'temperature'
model = 'HRDPS'

maxTileLat = 85.0511287798066
tileSize = 512  # px
minZoom = 2
maxZoom = 9


# tracemalloc.start()
modelDate = sys.argv[1]
modelHr = int(sys.argv[2])
forecastHr = int(sys.argv[3])
level = int(sys.argv[4])


dateSave = (datetime.strptime("%s %d" % (modelDate,modelHr),'%Y%m%d %H') + timedelta(hours=forecastHr)).strftime('%Y%m%d_%H')

nc = Dataset("CMC_hrdps_west_TMP_ISBL_%04d_ps2.5km_%s%02d_P%03d-00.nc" % (level, modelDate, modelHr, forecastHr), 'r')
var = nc.variables['t'][0,0].data - 273.15
missingValue = nc.variables['t'].missing_value

##  latitude, longitude, depth
lonNC = nc.variables['lon'][:].data
latNC = nc.variables['lat'][:].data
lonNC[lonNC >= 180] -= 360


# Mercator
R = 6378137
xNC = R * lonNC * np.pi/180.
yNC = R * np.log(np.tan(np.pi/4 + latNC*np.pi/180/2))


# Fixed min/max values for all levels and times
varMin = -100
step = 0.1

var[var==missingValue] = -9999
f = interpolate.interp2d(xNC, yNC, var, kind='linear')


###################################################################
###########################  FUNCTIONS  ###########################


def xMercator(lon):
    return R * lon * np.pi/180.


def yMercator(lat):
    return R * np.log(np.tan(np.pi/4 + lat*np.pi/180/2))


def saveImg(i, j):
    try:
        if(yTile[j*tileSize: (j+1)*tileSize].min() > yNC.max() or
           yTile[j*tileSize: (j+1)*tileSize].max() < yNC.min()):
            print('Exit 1')
            return
    except:
        print('Exit 2')
        return
    devNull = os.system('mkdir -p ../../tiles/%s_%s_%s_%04d/%d/%d' %
                        (model, field, dateSave, level, zoom, i))
    varNew = f(xTile[i*tileSize: (i+1)*tileSize],
                  yTile[j * tileSize:(j+1) * tileSize])
    varNew[varNew < varMin] = np.nan
    #
    # To trim the interpolation tail from the right side
    iLonMax = np.argmin(np.abs(xTile-xMercator(lonNC[-1])))
    if((i+1)*tileSize > iLonMax):
        if(i*tileSize > iLonMax):
            varNew[:, :] = np.nan
        else:
            varNew[:, iLonMax % tileSize:] = np.nan
    #
    # To trim the interpolation tail from the left side
    iLonMin = np.argmin(np.abs(xTile-xMercator(lonNC[0])))
    if(i*tileSize < iLonMin):
        if((i+1)*tileSize < iLonMin):
            varNew[:, :] = np.nan
        else:
            varNew[:, :iLonMin % tileSize] = np.nan
    #
    # To trim the interpolation tail from the top side
    jLatMax = np.argmin(np.abs(yTile-yMercator(latNC[-1])))
    if((j+1)*tileSize > jLatMax):
        if(j*tileSize > jLatMax):
            varNew[:, :] = np.nan
        else:
            varNew[jLatMax % tileSize:, :] = np.nan
    #
    # To trim the interpolation tail from the bottom side
    jLatMin = np.argmin(np.abs(yTile-yMercator(latNC[0])))
    if(j*tileSize < jLatMin):
        if((j+1)*tileSize < jLatMin):
            varNew[:, :] = np.nan
        else:
            varNew[:jLatMin % tileSize, :] = np.nan
    #
    if(np.isnan(np.nanmax(varNew))):
        return
    else:
        # Coloring
        varNewRounded = np.round(varNew, int(-math.log10(step)))
        varNewInt = ((varNewRounded-varMin)/step).astype(np.uint16)
        # Saving
        imageio.imwrite('../../tiles/%s_%s_%s_%04d/%d/%d/%d.png' % (model, field, dateSave, level,
                                                            zoom, i, 2**zoom-j-1), np.flipud(varNewInt))


def saveTile():
    global zoom
    global xTile, yTile
    #
    for zoom in np.arange(minZoom, maxZoom+1):
        print("--  Start zoom %d" % zoom)
        noOfPoints = 2**zoom*tileSize
        #
        xTile = np.linspace(xMercator(-180),
                            xMercator(180), noOfPoints)
        yTile = np.linspace(yMercator(-maxTileLat),
                            yMercator(maxTileLat), noOfPoints)
        iStart = math.floor(np.abs(xTile-xNC[0]).argmin()/tileSize)
        iEnd = math.floor(np.abs(xTile-xNC[-1]).argmin()/tileSize)+1
        jStart = math.floor(np.abs(yTile-yNC[0]).argmin()/tileSize)
        jEnd = math.floor(np.abs(yTile-yNC[-1]).argmin()/tileSize)+1
        iters = np.array(np.meshgrid(np.arange(iStart, iEnd),
                                     np.arange(jStart, jEnd))).T.reshape(-1, 2)
        #
        with multiprocessing.Pool() as p:
            p.starmap(saveImg, iters)


saveTile()
