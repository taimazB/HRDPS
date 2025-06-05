# import matplotlib.pyplot as plt
import os
import pandas as pd
import sys


fieldName = sys.argv[1]

PWD = os.getcwd()
scriptsDir = "%s/scripts" % PWD

sys.path.insert(0, scriptsDir)
from functions import *

fields = pd.read_json('scripts/fields.json')
process(fields[fields['name']==fieldName])





#     for i,fNC in enumerate(sorted(glob('HRDPS/%s/*.nc' % fieldName))):
#         fNC = os.path.basename(fNC)
#         dateTime = fNC.split('.')[0].split('_')[2:]
#         year = int(dateTime[0][:4])
#         month = int(dateTime[0][4:6])
#         day = int(dateTime[0][6:])
#         hour = int(dateTime[1])
#         # datetime_UTC = datetime(year, month, day, hour, tzinfo=utc)
#         #
#         # if(datetime_UTC.astimezone(minTZ).day==tomorrowDay or datetime_UTC.astimezone(maxTZ).day==tomorrowDay):
#         listExtracts.append([fieldName, CANADA, fNC])
#         listProcess.append([i, fNC, field[1], CANADA['cities']])

#     # with multiprocessing.Pool() as p:
#     #     values = p.map(extractNC, listExtracts)
        
    

#     with multiprocessing.Pool(8) as p:
#         df = pd.concat(p.map(process, listProcess), ignore_index=True)
#         df.to_csv(f'HRDPS/{fieldName}/CA/values/majors.csv', index=False)
#         # dfs.append(df)


# # commonKeys = list(filter(lambda x: 'dateTime' in x, dfs[0].keys()))+['i']
# # merged_df = pd.merge(dfs[0], dfs[1], on=commonKeys)
# # merged_df = pd.merge(merged_df, dfs[2], on=commonKeys)
# # merged_df = pd.merge(merged_df, dfs[3], on=commonKeys)
# # merged_df.to_csv('HRDPS/majors.csv', index=False)

# # dfs[0].to_csv('HRDPS/majors.csv', index=False)

# exit()




# #

# #
# for province in provinces.iterrows():
#     provinceShortName = province[1]['shortName']
#     lonMin = province[1]['lonMin']
#     lonMax = province[1]['lonMax']
#     latMin = province[1]['latMin']
#     latMax = province[1]['latMax']
#     timeZoneHr = province[1]['timeZoneHr']
#     cities = province[1]['cities']
#     #
#     devNull = os.system('mkdir -p "%s/HRDPS/%s/%s"' % (PWD, fieldName, provinceShortName))
#     devNull = os.system('cd %s/HRDPS/%s/ ; ls HRDPS*.nc | parallel "cdo sellonlatbox,%f,%f,%f,%f {} %s/{}"' % (PWD, fieldName, lonMin,lonMax,latMin,latMax,provinceShortName))
#     #
#     DT = datetime(today.year, today.month, today.day, timeZoneHr) + timedelta(days=1)
#     fileNames = []
#     for i in range(24):
#         fileName = "HRDPS_%s_%s" % (fieldName, DT.strftime("%Y%m%d_%H"))
#         if (os.path.exists("%s/HRDPS/%s/%s/%s.nc" % (PWD, fieldName,provinceShortName,fileName))):
#             fileNames.append(fileName)
#         DT = DT + timedelta(hours=1)
#     #
#     devNull = os.system('mkdir -p %s/HRDPS/%s/%s/tiles' % (PWD, fieldName, provinceShortName))
#     with multiprocessing.Pool() as p:
#         values = p.map(process, fileNames)
#     #
#     devNull = os.system('mkdir -p %s/HRDPS/%s/%s/values' % (PWD,fieldName, provinceShortName))
#     values = pd.DataFrame(list(itertools.chain(*values)))
#     for city in cities:
#         filter = values['city'] == city['name']
#         values[filter].sort_values(by=['fileName']).to_csv(
#             '%s/HRDPS/%s/%s/values/%s.csv' % (PWD,fieldName, provinceShortName, city['name']), index=False, columns=['value'], header=False)

#     np.savetxt('%s/HRDPS/%s/%s/values/extremes' % (PWD,fieldName, provinceShortName), np.array([values['min'].min(),values['max'].max()]), fmt='%f')

