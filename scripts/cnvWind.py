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


field = 'wind'
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

ncU = Dataset("CMC_hrdps_west_UGRD_ISBL_%04d_ps2.5km_%s%02d_P%03d-00.nc" % (level, modelDate, modelHr, forecastHr), 'r')
u = ncU.variables['u'][0,0].data

ncV = Dataset("CMC_hrdps_west_VGRD_ISBL_%04d_ps2.5km_%s%02d_P%03d-00.nc" % (level, modelDate, modelHr, forecastHr), 'r')
v = ncV.variables['v'][0,0].data


missingValue = ncU.variables['u'].missing_value

##  latitude, longitude, depth
lonNC = ncU.variables['lon'][:].data
latNC = ncU.variables['lat'][:].data
lonNC[lonNC >= 180] -= 360


# Mercator
R = 6378137
xNC = R * lonNC * np.pi/180.
yNC = R * np.log(np.tan(np.pi/4 + latNC*np.pi/180/2))


# Fixed min/max values for all levels and times
varMin = -100
step = 0.01

u[u==missingValue] = -9999
v[v==missingValue] = -9999
fU = interpolate.interp2d(xNC, yNC, u, kind='linear')
fV = interpolate.interp2d(xNC, yNC, v, kind='linear')


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
    devNull = os.system('mkdir -p ../../tilesU/%s_%s_%s_%04d/%d/%d' %
                        (model, field, dateSave, level, zoom, i))
    uNew = fU(xTile[i*tileSize: (i+1)*tileSize],
                  yTile[j * tileSize:(j+1) * tileSize])
    uNew[uNew < varMin] = np.nan
    #
    devNull = os.system('mkdir -p ../../tilesV/%s_%s_%s_%04d/%d/%d' %
                        (model, field, dateSave, level, zoom, i))
    vNew = fV(xTile[i*tileSize: (i+1)*tileSize],
                  yTile[j * tileSize:(j+1) * tileSize])
    vNew[vNew < varMin] = np.nan
    #
    # To trim the interpolation tail from the right side
    iLonMax = np.argmin(np.abs(xTile-xMercator(lonNC[-1])))
    if((i+1)*tileSize > iLonMax):
        if(i*tileSize > iLonMax):
            uNew[:, :] = np.nan
            vNew[:, :] = np.nan
        else:
            uNew[:, iLonMax % tileSize:] = np.nan
            vNew[:, iLonMax % tileSize:] = np.nan
    #
    # To trim the interpolation tail from the left side
    iLonMin = np.argmin(np.abs(xTile-xMercator(lonNC[0])))
    if(i*tileSize < iLonMin):
        if((i+1)*tileSize < iLonMin):
            uNew[:, :] = np.nan
            vNew[:, :] = np.nan
        else:
            uNew[:, :iLonMin % tileSize] = np.nan
            vNew[:, :iLonMin % tileSize] = np.nan
    #
    # To trim the interpolation tail from the top side
    jLatMax = np.argmin(np.abs(yTile-yMercator(latNC[-1])))
    if((j+1)*tileSize > jLatMax):
        if(j*tileSize > jLatMax):
            uNew[:, :] = np.nan
            vNew[:, :] = np.nan
        else:
            uNew[jLatMax % tileSize:, :] = np.nan
            vNew[jLatMax % tileSize:, :] = np.nan
    #
    # To trim the interpolation tail from the bottom side
    jLatMin = np.argmin(np.abs(yTile-yMercator(latNC[0])))
    if(j*tileSize < jLatMin):
        if((j+1)*tileSize < jLatMin):
            uNew[:, :] = np.nan
            vNew[:, :] = np.nan
        else:
            uNew[:jLatMin % tileSize, :] = np.nan
            vNew[:jLatMin % tileSize, :] = np.nan
    #
    if(np.isnan(np.nanmax(uNew))):
        return
    else:
        # Coloring
        uNewRounded = np.round(uNew, int(-math.log10(step)))
        uNewInt = ((uNewRounded-varMin)/step).astype(np.uint16)
        #
        vNewRounded = np.round(vNew, int(-math.log10(step)))
        vNewInt = ((vNewRounded-varMin)/step).astype(np.uint16)
        # Saving
        imageio.imwrite('../../tilesU/%s_%s_%s_%04d/%d/%d/%d.png' % (model, field, dateSave, level,
                                                            zoom, i, 2**zoom-j-1), np.flipud(uNewInt))
        imageio.imwrite('../../tilesV/%s_%s_%s_%04d/%d/%d/%d.png' % (model, field, dateSave, level,
                                                            zoom, i, 2**zoom-j-1), np.flipud(vNewInt))


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
