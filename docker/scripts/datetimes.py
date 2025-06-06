from glob import glob
import pytz
from datetime import datetime,timedelta
from pathlib import Path
import pandas as pd


CANADA = pd.read_json('scripts/provinces.json')
files = sorted(glob('nc/TMP/HRDPS*.nc'))
datetimes = ['_'.join(Path(f).stem.split('_')[2:]) for f in files]

utc = pytz.utc

for row in CANADA.iterrows():
    row = row[1]
    tz = pytz.timezone(row['timeZone'])
    datetimesLocal = [datetime.strptime(dt, '%Y%m%d_%H').replace(tzinfo=utc).astimezone(tz).strftime('%A, %B %d-%H:%M') for dt in datetimes]
    with open(f'data/tz_{row["shortName"]}.txt', 'w') as f:
        for dt in datetimesLocal:
            f.write(dt + '\n')
