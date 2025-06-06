date
# source ./configs.sh
export MAIN=$PWD
export MODEL=HRDPS

##  FIND LATEST MODEL RUN
lastAvailDateTime=$1

export GRIB2_DIR=${MAIN}/data/${MODEL}_grib2
export NC_DIR=${MAIN}/data/${MODEL}_nc

############################################################################
##  FUNCTIONS

function rename {
    f=$1
    varOrgIn=$2 ## eg t2
    varNew=$3   ## eg airTemperature
    remapType=$4

    date=$(date -d $(cdo -s showtimestamp $f) +%Y%m%d_%H)
    out=${MODEL}_${varNew}_${date}

    mkdir -p ${MAIN}/data/${MODEL}_nc/${varNew} 2>/dev/null

    cdo -f nc4 copy -${remapType},${MAIN}/scripts/grid.txt -chname,${varOrgIn},${varNew} $f ${MAIN}/data/${MODEL}_nc/${varNew}/${out}.nc.1
    cdo -z zip_1 -chname,lat,latitude -chname,lon,longitude ${MAIN}/data/${MODEL}_nc/${varNew}/${out}.nc.1 ${MAIN}/data/${MODEL}_nc/${varNew}/${out}.nc
    rm ${MAIN}/data/${MODEL}_nc/${varNew}/${out}.nc.* 2>/dev/null
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

    cdo merge ${NC_DIR}/windSpeed/${speedFile} ${NC_DIR}/windDirection/${directionFile} ${NC_DIR}/wind/${windFile}
}
export -f merge

function calcHumidex {
    tFile=$1
    dewFile=$(echo $tFile | sed "s/_TMP_/_DPT_/")
    humidexFile=$(echo $tFile | sed "s/_TMP_/_HUMIDEX_/")

    cdo -f nc merge ${NC_DIR}/TMP/${tFile} ${NC_DIR}/DPT/${dewFile} ${NC_DIR}/HUMIDEX/${humidexFile}
    ncap2 -O -s 'HUMIDEX=TMP + (3.39556)*2.71828^(19.8336 - 5417.75/(DPT+273.15)) - 5.5556' ${NC_DIR}/HUMIDEX/${humidexFile} ${NC_DIR}/HUMIDEX/${humidexFile}
    ncks -O -v HUMIDEX ${NC_DIR}/HUMIDEX/${humidexFile} ${NC_DIR}/HUMIDEX/${humidexFile}
}
export -f calcHumidex

function calcTotalRain {
    i=$1
    datetime=`ls | head -$i | tail -1 | cut -d_ -f3-4`
    cdo -O -z zip_1 enssum -chname,CONDALPCPN,TOTALRAIN `ls | head -$i` ${NC_DIR}/TOTALRAIN/HRDPS_TOTALRAIN_${datetime}
}
export -f calcTotalRain

function calcTotalSnow {
    i=$1
    datetime=`ls | head -$i | tail -1 | cut -d_ -f3-4`
    cdo -O -z zip_1 enssum -chname,CONDASSN,TOTALSNOW `ls | head -$i` ${NC_DIR}/TOTALSNOW/HRDPS_TOTALSNOW_${datetime}
}
export -f calcTotalSnow

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
    mkdir ${NC_DIR}/${dir}/geojson
    cd ${NC_DIR}/${dir}
    ls HRDPS_*.nc | xargs -I{} basename {} .nc | parallel 'nc2gj {} "${levels}"'

    cd ${NC_DIR}/${dir}/geojson
    python3 ~/scripts/mergeGJ.py

    ##  -pC: Don't compress (mapbox doesn't like it)
    ##  -pK: Don't skip tiles larger than 500K.
    tippecanoe -pC -pk -Z3 -z8 -l contour --drop-densest-as-needed merged.geojson -e ${NC_DIR}/${dir}/tiles
    cd ${MAIN}
    rm -r ${NC_DIR}/${dir}/geojson
}
export -f nc2pbf


##  FUNCTIONS
############################################################################

##  GRIB2 -> NC
rm -r ${NC_DIR} 2>/dev/null
mkdir ${NC_DIR}
cd ${GRIB2_DIR}

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
# ls *${lastDlDateTime}*-WEonG_CONDASSN*.grib2 | sort | parallel 'rename {} param156.1.0 CONDASSN remapbil' # Conditional amount of solid snow
# ls *${lastDlDateTime}*-WEonG_CONDAPL*.grib2 | sort | parallel 'rename {} param157.1.0 CONDAPL remapbil' # Conditional amount of solid ice pellets
# ls *${lastDlDateTime}*-WEonG_CONDAFZPCPN*.grib2 | sort | parallel 'rename {} param95.1.0 CONDAFZPCPN remapbil' # Conditional amount of freezing precipitation
# ls *${lastDlDateTime}*-WEonG_CONDAPCPN*.grib2 | sort | parallel 'rename {} param159.1.0 CONDAPCPN remapbil' # Conditional amount of precipitation
ls *${lastDlDateTime}*-WEonG_DPT*.grib2 | sort | parallel 'rename {} 2d DPT remapbil' # Dew point temperature
# ls *${lastDlDateTime}*-WEonG_GUST*.grib2 | sort | parallel 'rename {} i10fg GUST remapbil' # Gust
# ls *${lastDlDateTime}*-WEonG_HGTSNLVL*.grib2 | sort | parallel 'rename {} param40.19.0 HGTSNLVL remapbil' # Height of snow level
ls *${lastDlDateTime}*-WEonG_TMP*.grib2 | sort | parallel 'rename {} 2t TMP remapbil' # Temperature
# ls *${lastDlDateTime}*-WEonG_WDIR*.grib2 | sort | parallel 'rename {} 10wdir WDIR remapbil' # Wind direction
ls *${lastDlDateTime}*-WEonG_WSPD*.grib2 | sort | parallel 'rename {} 10si WSPD remapbil' # Wind speed
# ls *${lastDlDateTime}*TCDC*.grib2 | sort | parallel 'rename {} param1.6.0 TCDC remapbil' # Total cloud cover
# ls *${lastDlDateTime}*PRMSL*.grib2 | sort | parallel 'rename {} prmsl PRMSL remapbil' # Pressure reduced to MSL
# ls *${lastDlDateTime}*_RH_AGL-2m*.grib2 | sort | parallel 'rename {} 2r RH remapbil' # 2m relative humidity

##  K -> C
cd ${NC_DIR}/TMP
ls *_TMP_*.nc | parallel 'K2C {}'
cd ${NC_DIR}/DPT
ls *_DPT_*.nc | parallel 'K2C {}'

##  m/s -> km/hr
cd ${NC_DIR}/WSPD
ls *.nc | parallel 'cnvSpeed {}'
# cd ${MAIN}/nc/GUST
# ls *.nc | parallel 'cnvSpeed {}'

# ##  HUMIDEX
# cd ${NC_DIR}/TMP
# mkdir -p ${NC_DIR}/HUMIDEX
# ls HRDPS*.nc | parallel 'calcHumidex {}'

# ##  Pa -> hPa
# cd ${MAIN}/nc/PRMSL
# ls *.nc | parallel 'cnvPressure {}'

## m -> mm
for d in CONDALPCPN; do # CONDAFZPCPN CONDAPCPN
    cd ${NC_DIR}/$d
    ls *.nc | parallel 'cnvMmm {}'
done

## m -> cm
# for d in CONDASSN; do # CONDAPL
#     cd ${MAIN}/nc/$d
#     ls *.nc | parallel 'cnvMcm {}'
# done

##  REMOVE UNWANTED DIMENSIONS
cd ${NC_DIR}
find . -name *.nc | parallel 'removeDims {}'

##  TOTAL RAIN
mkdir ${NC_DIR}/TOTALRAIN
cd ${NC_DIR}/CONDALPCPN
n=`ls HRDPS*.nc | wc -l`
parallel 'calcTotalRain {}' ::: `seq 1 $n`

##  TOTAL SNOW
# mkdir ${MAIN}/nc/TOTALSNOW
# cd ${MAIN}/nc/CONDASSN
# n=`ls | wc -l`
# parallel 'calcTotalSnow {}' ::: `seq 1 $n`

cd ${MAIN}
for field in TMP CONDALPCPN WSPD TOTALRAIN; do # HUMIDEX CONDASSN TOTALSNOW GUST
    python3 scripts/cnv.py ${MODEL} ${field}
done

date
