#!/bin/bash

#SBATCH --job-name=HRDPS
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --time=12:00:00
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
#SBATCH --priority=2001

date
source ./configs.sh

##  FIND LATEST MODEL RUN
lastDlDateTime=$(cat ${MAIN}/.lastDlDateTime)

############################################################################
##  FUNCTIONS

function rename {
    f=$1
    varOrgIn=$2 ## eg t2
    varNew=$3   ## eg airTemperature
    remapType=$4

    date=$(date -d $(cdo -s showtimestamp $f) +%Y%m%d_%H)
    out=${MODEL}_${varNew}_${date}

    mkdir -p ${MAIN}/nc/${varNew} 2>/dev/null

    cdo -f nc4 copy -${remapType},${MAIN}/scripts/grid.txt -chname,${varOrgIn},${varNew} $f ${MAIN}/nc/${varNew}/${out}.nc.1
    cdo -z zip_1 -chname,lat,latitude -chname,lon,longitude ${MAIN}/nc/${varNew}/${out}.nc.1 ${MAIN}/nc/${varNew}/${out}.nc
    rm ${MAIN}/nc/${varNew}/${out}.nc.* 2>/dev/null
}
export -f rename

function mergeTime {
    var=$1
    cdo mergetime ${MAIN}/nc/${var}/*.nc ${MAIN}/nc/merged/${MODEL}_${var}.nc.1
    cdo -z zip_1 -intntime,12 HRDPS_airTemperature.nc.1 ${MAIN}/nc/merged/${MODEL}_${var}.nc
    rm ${MAIN}/nc/merged/${MODEL}_${var}.nc.1 2>/dev/null
}
export -f mergeTime

function removeDims {
    f=$1
    ncwa -O -a time,height ${f} ${f}.1
    mv ${f}.1 ${f}
    rm ${f}.* 2>/dev/null
}
export -f removeDims

##  Convert Kelvin to Centigrade
function K2C {
    f=$1
    var=$(echo $f | cut -d_ -f2)
    ncap2 -O -s "${var}-=273.15" $f $f
}
export -f K2C

function cnvSpeed {
    f=$1
    var=$(echo $f | cut -d_ -f2)
    ncap2 -O -s "${var}*=3.6" $f $f
}
export -f cnvSpeed

function cnvPressure {
    ##  Pa -> hPa
    f=$1
    var=$(echo $f | cut -d_ -f2)
    ncap2 -O -s "${var}/=100" $f $f
}
export -f cnvPressure

function cnvMmm {
    ##  M -> mm
    f=$1
    var=$(echo $f | cut -d_ -f2)
    ncap2 -O -s "${var}*=1000" $f $f
}
export -f cnvMmm

function cnvMcm {
    ##  M -> mm
    f=$1
    var=$(echo $f | cut -d_ -f2)
    ncap2 -O -s "${var}*=100" $f $f
}
export -f cnvMcm

function merge {
    speedFile=$1
    directionFile=$(echo $speedFile | sed "s/_windSpeed_/_windDirection_/")
    windFile=$(echo $speedFile | sed "s/_windSpeed_/_wind_/")

    cdo merge ${MAIN}/nc/windSpeed/${speedFile} ${MAIN}/nc/windDirection/${directionFile} ${MAIN}/nc/wind/${windFile}
}
export -f merge

function calcHumidex {
    tFile=$1
    dewFile=$(echo $tFile | sed "s/_TMP_/_DPT_/")
    humidexFile=$(echo $tFile | sed "s/_TMP_/_HUMIDEX_/")

    cdo -f nc merge ${MAIN}/nc/TMP/${tFile} ${MAIN}/nc/DPT/${dewFile} ${MAIN}/nc/HUMIDEX/${humidexFile}
    ncap2 -O -s 'HUMIDEX=TMP + (3.39556)*2.71828^(19.8336 - 5417.75/(DPT+273.15)) - 5.5556' ${MAIN}/nc/HUMIDEX/${humidexFile} ${MAIN}/nc/HUMIDEX/${humidexFile}
    ncks -O -v HUMIDEX ${MAIN}/nc/HUMIDEX/${humidexFile} ${MAIN}/nc/HUMIDEX/${humidexFile}
}
export -f calcHumidex

function calcTotalRain {
    i=$1
    datetime=`ls | head -$i | tail -1 | cut -d_ -f3-4`
    cdo -O -z zip_1 enssum -chname,CONDALPCPN,TOTALRAIN `ls | head -$i` ${MAIN}/nc/TOTALRAIN/HRDPS_TOTALRAIN_${datetime}
}
export -f calcTotalRain

function nc2gj {
    f=$1 ##  WITHOUT extension
    levels=$2
    gdal_contour -b 1 -fl ${levels} -amin min -amax max -p $f.nc $f.geojson
    ##  Update GJ properties
    dateTime=$(echo $f | cut -d_ -f3-4)
    cat $f.geojson | jq ".features[].properties.datetime = \"${dateTime}\"" >geojson/$f.geojson
    rm $f.geojson
}
export -f nc2gj

function nc2pbf {
    dir=$1
    export levels=$2
    mkdir ${MAIN}/nc/${dir}/geojson
    cd ${MAIN}/nc/${dir}
    ls HRDPS_*.nc | xargs -I{} basename {} .nc | parallel 'nc2gj {} "${levels}"'

    cd ${MAIN}/nc/${dir}/geojson
    python3 ~/scripts/mergeGJ.py

    ##  -pC: Don't compress (mapbox doesn't like it)
    ##  -pK: Don't skip tiles larger than 500K.
    tippecanoe -pC -pk -Z3 -z8 -l contour --drop-densest-as-needed merged.geojson -e ${MAIN}/nc/${dir}/tiles
    cd ${MAIN}
    rm -r ${MAIN}/nc/${dir}/geojson
}
export -f nc2pbf

function sync {
    # dir=$1
    # cd ${MAIN}/nc/${dir}

    # rsync -ar -e "ssh -p ${SERVER_PORT}" . ${SERVER_IP}:${SERVER_DIR}/${dir}_${lastDlDateTime}/
    
    #T rsync -ar -e "ssh -p ${SERVER_PORT}" ${MAIN}/nc ${SERVER_IP}:${SERVER_DIR}/
    #T rsync -ar -e "ssh -p ${SERVER_PORT}" ${MAIN}/data ${SERVER_IP}:${SERVER_DIR}/
    rsync -ar --delete ${MAIN}/nc taimaz.ddns.net:/home/taimaz/Projects/Blender/Projects/weather/
    rsync -ar --delete ${MAIN}/data taimaz.ddns.net:/home/taimaz/Projects/Blender/Projects/weather/nc/
}

function finalize {
    ssh -p ${SERVER_PORT} ${SERVER_IP} <<EOF
cd ${SERVER_DIR}/nc
for dir in *; do
rm -r ../\${dir}
mv \${dir} ..
done

cd ${SERVER_DIR}
ls TMP/*2*.nc | xargs -I{} basename {} .nc | cut -d_ -f 3-4 > .availDateTimes
rm -r ${SERVER_DIR}/nc
EOF
}

##  FUNCTIONS
############################################################################

##  GRIB2 -> NC
rm -r ${MAIN}/nc 2>/dev/null
mkdir ${MAIN}/nc
cd ${MAIN}/grib2

##  RENAME FILES FOR TILE GENERATION
# ls *${lastDlDateTime}*-WEonG_PROBFZRA*.grib2 | sort | parallel 'rename {} cfrzr PROBFZRA remapbil' # Probability of freezing rain
# ls *${lastDlDateTime}*-WEonG_PROBPL*.grib2 | sort | parallel 'rename {} cicep PROBPL remapbil' # Probability of ice pellets
# ls *${lastDlDateTime}*-WEonG_PROBRA*.grib2 | sort | parallel 'rename {} crain PROBRA remapbil' # Probability of rain
# ls *${lastDlDateTime}*-WEonG_PROBSN*.grib2 | sort | parallel 'rename {} param36.19.0 PROBSN remapbil' # Probability of snow
# ls *${lastDlDateTime}*-WEonG_PROBLPCPN*.grib2 | sort | parallel 'rename {} param151.1.0 PROBLPCPN remapbil' # Probability of liquid precipitation
# ls *${lastDlDateTime}*-WEonG_PROBBLSN*.grib2 | sort | parallel 'rename {} param125.1.0 PROBBLSN remapbil' # Probability of blowing snow
# ls *${lastDlDateTime}*-WEonG_PROBDZ*.grib2 | sort | parallel 'rename {} param152.1.0 PROBDZ remapbil' # Probability of drizzle
# ls *${lastDlDateTime}*-WEonG_PROBFZDZ*.grib2 | sort | parallel 'rename {} param153.1.0 PROBFZDZ remapbil' # Probability of freezing drizzle
# ls *${lastDlDateTime}*-WEonG_PROBFZPCPN*.grib2 | sort | parallel 'rename {} param150.1.0 PROBFZPCPN remapbil' # Probability of freezing precipitation
# ls *${lastDlDateTime}*-WEonG_PROBPCPN*.grib2 | sort | parallel 'rename {} pop PROBPCPN remapbil' # Probability of precipitation
# ls *${lastDlDateTime}*-WEonG_PROBTSOCRNC*.grib2 | sort | parallel 'rename {} tstm PROBTSOCRNC remapbil' # Probability of thunderstorm occurrence
# ls *${lastDlDateTime}*-WEonG_PROBSNSQ*.grib2 | sort | parallel 'rename {} param36.19.0 PROBSNSQ remapbil' # Probability of snow squalls
ls *${lastDlDateTime}*-WEonG_CONDALPCPN*.grib2 | sort | parallel 'rename {} param158.1.0 CONDALPCPN remapbil' # Conditional amount of liquid precipitation
ls *${lastDlDateTime}*-WEonG_CONDASSN*.grib2 | sort | parallel 'rename {} param156.1.0 CONDASSN remapbil' # Conditional amount of solid snow
# ls *${lastDlDateTime}*-WEonG_CONDAPL*.grib2 | sort | parallel 'rename {} param157.1.0 CONDAPL remapbil' # Conditional amount of solid ice pellets
# ls *${lastDlDateTime}*-WEonG_CONDAFZPCPN*.grib2 | sort | parallel 'rename {} param95.1.0 CONDAFZPCPN remapbil' # Conditional amount of freezing precipitation
# ls *${lastDlDateTime}*-WEonG_CONDAPCPN*.grib2 | sort | parallel 'rename {} param159.1.0 CONDAPCPN remapbil' # Conditional amount of precipitation
ls *${lastDlDateTime}*-WEonG_DPT*.grib2 | sort | parallel 'rename {} 2d DPT remapbil' # Dew point temperature
# ls *${lastDlDateTime}*-WEonG_GUST*.grib2 | sort | parallel 'rename {} gust GUST remapbil' # Gust
# ls *${lastDlDateTime}*-WEonG_HGTSNLVL*.grib2 | sort | parallel 'rename {} param40.19.0 HGTSNLVL remapbil' # Height of snow level
ls *${lastDlDateTime}*-WEonG_TMP*.grib2 | sort | parallel 'rename {} 2t TMP remapbil' # Temperature
# ls *${lastDlDateTime}*-WEonG_WDIR*.grib2 | sort | parallel 'rename {} 10wdir WDIR remapbil' # Wind direction
ls *${lastDlDateTime}*-WEonG_WSPD*.grib2 | sort | parallel 'rename {} 10si WSPD remapbil' # Wind speed
# ls *${lastDlDateTime}*TCDC*.grib2 | sort | parallel 'rename {} param1.6.0 TCDC remapbil' # Total cloud cover
# ls *${lastDlDateTime}*PRMSL*.grib2 | sort | parallel 'rename {} prmsl PRMSL remapbil' # Pressure reduced to MSL
# ls *${lastDlDateTime}*_RH_AGL-2m*.grib2 | sort | parallel 'rename {} 2r RH remapbil' # 2m relative humidity

##  K -> C
cd ${MAIN}/nc/TMP
ls *_TMP_*.nc | parallel 'K2C {}'
cd ${MAIN}/nc/DPT
ls *_DPT_*.nc | parallel 'K2C {}'

##  m/s -> km/hr
cd ${MAIN}/nc/WSPD
ls *.nc | parallel 'cnvSpeed {}'
# cd ${MAIN}/nc/GUST
# ls *.nc | parallel 'cnvSpeed {}'

##  HUMIDEX
cd ${MAIN}/nc/TMP
mkdir -p ${MAIN}/nc/HUMIDEX
ls HRDPS*.nc | parallel 'calcHumidex {}'

# ##  Pa -> hPa
# cd ${MAIN}/nc/PRMSL
# ls *.nc | parallel 'cnvPressure {}'

## m -> mm
for d in CONDALPCPN; do # CONDAFZPCPN CONDAPCPN
    cd ${MAIN}/nc/$d
    ls *.nc | parallel 'cnvMmm {}'
done

## m -> cm
for d in CONDASSN; do # CONDAPL
    cd ${MAIN}/nc/$d
    ls *.nc | parallel 'cnvMcm {}'
done

##  REMOVE UNWANTED DIMENSIONS
cd ${MAIN}/nc
find . -name *.nc | parallel 'removeDims {}'

## EXTRACT STATIONS
# cd ${MAIN}/nc
# parallel 'python3 ${MAIN}/scripts/stations.py {} linear' ::: CONDAFZPCPN CONDAPCPN CONDASSN GUST PRMSL PROBDZ PROBFZPCPN PROBLPCPN PROBPL PROBSN PROBTSOCRNC RH TMP WSPD CONDALPCPN CONDAPL DPT HGTSNLVL PROBBLSN PROBFZDZ PROBFZRA PROBPCPN PROBRA PROBSNSQ TCDC WDIR

##  MERGE DATETIMES
# cd ${MAIN}/nc
# for d in *; do
#     cdo -O -z zip_1 merge ${d}/HRDPS_* ${d}/all.nc
# done

##  TOTAL RAIN
mkdir ${MAIN}/nc/TOTALRAIN
cd ${MAIN}/nc/CONDALPCPN
n=`ls | wc -l`
parallel 'calcTotalRain {}' ::: `seq 1 $n`


date

cd ${MAIN}
parallel 'python3 scripts/cnv.py' ::: TMP CONDALPCPN CONDASSN WSPD TOTALRAIN HUMIDEX
python3 scripts/datetimes.py {}


# SYNC
(
    sync
    finalize
    # rsync -aur -e 'ssh -p 4413' nc root@cloudzy.ddns.net:
    rm -r ${MAIN}/grib2 ${MAIN}/nc
    rm ${MAIN}/.active
) &
