import numpy as np
from netCDF4 import Dataset
# import matplotlib.pyplot as plt
import multiprocessing
import os
import imageio
from PIL import ImageColor
from datetime import datetime, timedelta
from glob import glob
import pandas as pd
import pytz
import json
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,  # or logging.DEBUG for more details
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)


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
    #
    lastColor = list(ImageColor.getcolor(colors[-1], 'RGBA'))
    allColors = np.concatenate((allColors, [lastColor]), axis=0)
    return allColors


# def extractProvince(item):
#     province, lonNC, latNC, var, fieldName, varMin, varMax, fieldStep = item
#     devNull = os.system(f'mkdir -p nc/{fieldName}/images/{province}')
#     devNull = os.system(f'mkdir -p nc/{fieldName}/data')
#     #
#     ##  EXTRACT CITIES
#     cities = pd.read_csv(f'scripts/cities.csv')
#     selectedCities = cities[cities['province']==province]
#     df = {}
#     df['datetime'] = datetimes(selectedCities['tz'].iloc[0], fieldName)
#     for row in selectedCities.iterrows():
#         id = row[1]['id']
#         lon = row[1]['lon']
#         lat = row[1]['lat']
#         iLon = np.argmin(np.abs(lonNC-lon))
#         iLat = np.argmin(np.abs(latNC-lat))
#         values = []
#         for var_t in var:
#             values.append(var_t[iLat,iLon])
#         df[f"city_{id}"] = values
#     #
#     df = pd.DataFrame(data=df)
#     df.to_csv(f'nc/{fieldName}/data/{province}.csv',index=None)
#     #
#     with open(f'topos/geojson/{province}.geojson') as f:
#         geojson_data = json.load(f)
#     #
#     boundary_polygon = shape(geojson_data['features'][0]['geometry'])
#     lonMin, latMin, lonMax, latMax = boundary_polygon.bounds
#     #
#     iLonMin = np.argmin(np.abs(lonNC-lonMin))
#     iLonMax = np.argmin(np.abs(lonNC-lonMax))
#     iLatMin = np.argmin(np.abs(latNC-latMin))
#     iLatMax = np.argmin(np.abs(latNC-latMax))
#     #
#     lonSub = lonNC[iLonMin:iLonMax+1]
#     latSub = latNC[iLatMin:iLatMax+1]
#     varSub = var[:, iLatMin:iLatMax+1, iLonMin:iLonMax+1]
#     #
#     lonGrid, latGrid = np.meshgrid(lonSub, latSub)
#     mask = np.array([boundary_polygon.contains(Point(lon, lat))
#                     for lon, lat in zip(lonGrid.ravel(), latGrid.ravel())])
#     mask = mask.reshape(varSub[0, :, :].shape)
#     #
#     offset = 0.1
#     maxPixelValue = 2**16-1
#     for i, varStep in enumerate(varSub):
#         varStep = varStep.data
#         varStep += offset # TO PRESERVE PROVINCE BOUNDARIES FOR FIELDS LIKE RAIN AND SNOW
#         varStep[varStep < varMin] = varMin
#         varStep[varStep > varMax] = varMax
#         varStep[~mask] = np.nan
#         varNewInt = maxPixelValue*(varStep - varMin) / (varMax - varMin)
#         varNewInt[np.isnan(varNewInt)] = 0
#         varNewInt = varNewInt.astype(np.uint16)
#         output = f"nc/{fieldName}/images/{province}/f{'%03d' % (i+1)}.png"
#         imageio.imwrite(output, np.flipud(varNewInt))


def genImage(item):
    logger = logging.getLogger(__name__)
    start_time = datetime.now()
    logger.info(f"Starting genImage processing at {start_time}")
    #
    MODEL,var, fieldName, varMin, varMax, step = item
    logger.info(f"Processing field: {fieldName}, var shape: {var.shape}")
    #
    #
    # Process geojson (note: this uses the last province from loop above)
    # geojson_start = datetime.now()
    # logger.info(f"Processing geojson for province: {province}")
    # with open(f'topos/geojson/{province}.geojson') as f:
    #     geojson_data = json.load(f)
    #
    # boundary_polygon = shape(geojson_data['features'][0]['geometry'])
    # lonMin, latMin, lonMax, latMax = boundary_polygon.bounds
    #
    # iLonMin = np.argmin(np.abs(lonNC-lonMin))
    # iLonMax = np.argmin(np.abs(lonNC-lonMax))
    # iLatMin = np.argmin(np.abs(latNC-latMin))
    # iLatMax = np.argmin(np.abs(latNC-latMax))
    #
    # lonSub = lonNC[iLonMin:iLonMax+1]
    # latSub = latNC[iLatMin:iLatMax+1]
    # varSub = var[:, iLatMin:iLatMax+1, iLonMin:iLonMax+1]
    #
    # lonGrid, latGrid = np.meshgrid(lonSub, latSub)
    # mask = np.array([boundary_polygon.contains(Point(lon, lat))
    #                 for lon, lat in zip(lonGrid.ravel(), latGrid.ravel())])
    # mask = mask.reshape(varSub[0, :, :].shape)
    #
    # geojson_time = (datetime.now() - geojson_start).total_seconds()
    # logger.info(f"Geojson processing completed in {geojson_time:.2f}s")
    #
    # Generate images
    images_start = datetime.now()
    logger.info("Starting image generation")
    offset = 0.1
    # mask = var[0].mask
    #
    # Prepare items for parallel processing
    items = []
    for i, varStep in enumerate(var):
        items.append((MODEL,i, varStep, offset, varMin, varMax, step, fieldName, allColors))
    #
    # Use multiprocessing to process images in parallel
    with multiprocessing.Pool() as pool:
        results = pool.map(process_single_image, items)
    #
    logger.info(f"Processed {len(results)} images in parallel")
    #
    images_time = (datetime.now() - images_start).total_seconds()
    total_time = (datetime.now() - start_time).total_seconds()
    #
    logger.info(f"Image generation completed in {images_time:.2f}s ({len(var)} images)")
    logger.info(f"Total genImage runtime: {total_time:.2f}s")


def process_single_image(item):
    MODEL, i, varStep, offset, varMin, varMax, step, fieldName, allColors = item
    #
    varStep = varStep.copy()  # Make a copy to avoid modifying original
    varStep += offset # TO PRESERVE PROVINCE BOUNDARIES FOR FIELDS LIKE RAIN AND SNOW
    varStep[varStep < varMin] = varMin
    varStep[varStep > varMax] = varMax
    #
    # Convert to integer indices
    varNewInt = np.int16((varStep - varMin)/step)
    varNewInt[np.isnan(varNewInt)] = 0
    #
    # Apply color mapping
    varColors = allColors[varNewInt].astype(np.uint8)
    #
    # Save image
    output = f"data/{MODEL}_nc/{fieldName}/images/f{'%03d' % (i+1)}.png"
    imageio.imwrite(output, np.flipud(varColors))
    #
    return i + 1

def datetimes(dateTimes, timeZone):
    utc = pytz.utc
    tz = pytz.timezone(timeZone)
    #
    dates_local = [dt.replace(tzinfo=utc).astimezone(tz).strftime('%A, %B %d') for dt in dateTimes]
    times_local = [dt.replace(tzinfo=utc).astimezone(tz).strftime('%H:%M') for dt in dateTimes]
    return dates_local, times_local


def extractCities(MODEL,fieldName,lonNC, latNC, dateTimes, var):
    logger = logging.getLogger(__name__)
    logger.info(f"Starting cities extraction for field: {fieldName}")
    #
    cities_start = datetime.now()
    cities = pd.read_csv(f'scripts/cities.csv')
    df = {}
    #
    for province in ['N', 'L', 'NS', 'NB', 'QC', 'ON', 'MB', 'SK', 'AB', 'BC']:
        province_start = datetime.now()
        selectedCities = cities[cities['province']==province]
        df[province] = {}
        df[province]['dates'], df[province]['times'] = datetimes(dateTimes, selectedCities['tz'].iloc[0])
        #
        for row in selectedCities.iterrows():
            id = row[1]['id']
            lon = row[1]['lon']
            lat = row[1]['lat']
            iLon = np.argmin(np.abs(lonNC-lon))
            iLat = np.argmin(np.abs(latNC-lat))
            values = []
            for var_t in var:
                values.append(int(round(float(var_t[iLat,iLon]))))
            df[province][f"city_{id}"] = values
        #
        province_time = (datetime.now() - province_start).total_seconds()
        logger.debug(f"Province {province} processed in {province_time:.2f}s")
    #
    cities_time = (datetime.now() - cities_start).total_seconds()
    logger.info(f"Cities extraction completed in {cities_time:.2f}s")
    #
    # Save cities data
    json.dump(df, open(f'data/{MODEL}_nc/{fieldName}/data/cities.json', 'w'), indent=4)
    logger.info(f"Cities data saved to data/{MODEL}_nc/{fieldName}/data/cities.json")


def process(MODEL, field):
    logger = logging.getLogger(__name__)
    start_time = datetime.now()
    #
    fieldName = field['name'].iloc[0]
    stops = field['stops'].iloc[0]
    colors = field['colors'].iloc[0]
    step = field['step'].iloc[0]
    #
    logger.info(f"Starting process for field: {fieldName}")
    logger.debug(f"Field parameters - stops: {stops}, colors: {colors}, step: {step}")
    #
    # Create directories and merge files
    logger.info("Creating directories and merging NetCDF files")
    devNull = os.system(f'cdo -O merge data/{MODEL}_nc/{fieldName}/{MODEL}*.nc data/{MODEL}_nc/{fieldName}/all.nc')
    devNull = os.system(f'mkdir -p data/{MODEL}_nc/{fieldName}/images')
    devNull = os.system(f'mkdir -p data/{MODEL}_nc/{fieldName}/data')
    #
    # Load NetCDF data
    logger.info(f"Loading NetCDF data from data/{MODEL}_nc/{fieldName}/all.nc")
    nc_start = datetime.now()
    nc = Dataset(f"data/{MODEL}_nc/{fieldName}/all.nc")
    var = nc.variables[fieldName][:]
    #
    # latitude, longitude
    lonNC = nc.variables['longitude'][:].data
    latNC = nc.variables['latitude'][:].data
    nc_time = (datetime.now() - nc_start).total_seconds()
    #
    # Original dateTimes
    files = sorted(glob(f'data/{MODEL}_nc/{fieldName}/{MODEL}*.nc'))
    dateTimes = [datetime.strptime('_'.join(Path(f).stem.split('_')[2:]), '%Y%m%d_%H') for f in files]
    #
    logger.info(f"NetCDF data loaded in {nc_time:.2f}s - var shape: {var.shape}, lon range: [{lonNC.min():.2f}, {lonNC.max():.2f}], lat range: [{latNC.min():.2f}, {latNC.max():.2f}]")
    #
    # Set variable bounds
    varMin = stops[0]
    varMax = stops[-1]
    logger.info(f"Variable bounds - min: {varMin}, max: {varMax}")
    #
    # Generate color palette
    logger.info("Generating color palette")
    color_start = datetime.now()
    global allColors
    allColors = genColors(stops, colors, step)
    color_time = (datetime.now() - color_start).total_seconds()
    logger.info(f"Color palette generated in {color_time:.2f}s with {len(allColors)} colors")
    #
    # Interpolate variable over time axis
    logger.info("Starting temporal interpolation")
    interp_start = datetime.now()
    time_indices = np.arange(0, var.shape[0], 1/6)  # Every 10 minutes
    original_indices = np.arange(var.shape[0])
    #
    logger.debug(f"Interpolating from {var.shape[0]} to {len(time_indices)} time steps")
    #
    # Reshape for vectorized interpolation
    var_reshaped = var.reshape(var.shape[0], -1)
    varInterp = np.empty((len(time_indices), var_reshaped.shape[1]))
    #
    # Interpolate dateTimes
    dateTimes_interp = [dateTimes[0] + timedelta(minutes=10 * i) for i in range(len(time_indices))]
    #
    for i in range(var_reshaped.shape[1]):
        varInterp[:, i] = np.interp(time_indices, original_indices, var_reshaped[:, i])
    #
    varInterp = varInterp.reshape(-1, var.shape[1], var.shape[2])
    varInterp[:,var[0].mask] = np.nan  # Preserve mask from original variable
    interp_time = (datetime.now() - interp_start).total_seconds()
    logger.info(f"Temporal interpolation completed in {interp_time:.2f}s - new shape: {varInterp.shape}")
    #
    # Extract cities data
    logger.info("Extracting cities data")
    extractCities(MODEL,fieldName, lonNC, latNC, dateTimes_interp, varInterp)
    #
    # Generate images
    logger.info("Starting image generation")
    genImage((MODEL, varInterp, fieldName, varMin, varMax, step))
    #
    total_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Process completed for field {fieldName} in {total_time:.2f}s")
