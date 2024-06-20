source ./configs.sh

field=$1
i=$2          ## Number of days in the future (0: today, 1: tomorrow)

if [[ -z ${field} ]] || [[ -z $i ]]; then
    echo "##  WRONG ARGUMENTS"
    exit 1
fi

day=`date -d "+${i} day" +%Y%m%d`
dayAfter=`date -d "+$((i+1)) day" +%Y%m%d`

cd ${MAIN}/nc/${field}

PR=NL
cdo -O ensmin HRDPS_${field}_${day}_{03..23}.nc HRDPS_${field}_${dayAfter}_{00..02}.nc HRDPS_${field}_day_min_${PR}.nc
cdo -O ensmax HRDPS_${field}_${day}_{03..23}.nc HRDPS_${field}_${dayAfter}_{00..02}.nc HRDPS_${field}_day_max_${PR}.nc
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_min_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_max_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1


PR=NS
cdo -O ensmin HRDPS_${field}_${day}_{04..23}.nc HRDPS_${field}_${dayAfter}_{00..03}.nc HRDPS_${field}_day_min_${PR}.nc
cdo -O ensmax HRDPS_${field}_${day}_{04..23}.nc HRDPS_${field}_${dayAfter}_{00..03}.nc HRDPS_${field}_day_max_${PR}.nc
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_min_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_max_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1


PR=QC
cdo -O ensmin HRDPS_${field}_${day}_{05..23}.nc HRDPS_${field}_${dayAfter}_{00..04}.nc HRDPS_${field}_day_min_${PR}.nc
cdo -O ensmax HRDPS_${field}_${day}_{05..23}.nc HRDPS_${field}_${dayAfter}_{00..04}.nc HRDPS_${field}_day_max_${PR}.nc
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_min_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_max_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1


## ON
cp HRDPS_${field}_day_min_${PR}.nc HRDPS_${field}_day_min_ON.nc
cp HRDPS_${field}_day_max_${PR}.nc HRDPS_${field}_day_max_ON.nc
cp -r tiles/HRDPS_${field}_day_min_${PR} tiles/HRDPS_${field}_day_min_ON
cp -r tiles/HRDPS_${field}_day_max_${PR} tiles/HRDPS_${field}_day_max_ON


PR=MN
cdo -O ensmin HRDPS_${field}_${day}_{06..23}.nc HRDPS_${field}_${dayAfter}_{00..05}.nc HRDPS_${field}_day_min_${PR}.nc
cdo -O ensmax HRDPS_${field}_${day}_{06..23}.nc HRDPS_${field}_${dayAfter}_{00..05}.nc HRDPS_${field}_day_max_${PR}.nc
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_min_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_max_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1


## SK
cp HRDPS_${field}_day_min_${PR}.nc HRDPS_${field}_day_min_SK.nc
cp HRDPS_${field}_day_max_${PR}.nc HRDPS_${field}_day_max_SK.nc
cp -r tiles/HRDPS_${field}_day_min_${PR} tiles/HRDPS_${field}_day_min_SK
cp -r tiles/HRDPS_${field}_day_max_${PR} tiles/HRDPS_${field}_day_max_SK


PR=AL
cdo -O ensmin HRDPS_${field}_${day}_{07..23}.nc HRDPS_${field}_${dayAfter}_{00..06}.nc HRDPS_${field}_day_min_${PR}.nc
cdo -O ensmax HRDPS_${field}_${day}_{07..23}.nc HRDPS_${field}_${dayAfter}_{00..06}.nc HRDPS_${field}_day_max_${PR}.nc
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_min_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_max_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1


PR=BC
cdo -O ensmin HRDPS_${field}_${day}_{08..23}.nc HRDPS_${field}_${dayAfter}_{00..07}.nc HRDPS_${field}_day_min_${PR}.nc
cdo -O ensmax HRDPS_${field}_${day}_{08..23}.nc HRDPS_${field}_${dayAfter}_{00..07}.nc HRDPS_${field}_day_max_${PR}.nc
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_min_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
python3 ~/scripts/cnvMaster_RGBcoded.py --fileName=HRDPS_${field}_day_max_${PR} --minZoom=3 --maxZoom=8 --minOrg=-100 --step=0.1
