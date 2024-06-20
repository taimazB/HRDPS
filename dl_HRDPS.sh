#!/bin/bash
export dlLink="https://dd.weather.gc.ca/model_hrdps/continental/2.5km"

############################################################################

source ./configs.sh

lasts=()
for hr in 00 06 12 18; do
    last=`curl -s ${dlLink}/${hr}/048/ | grep grib2 | sed 's/.*"\(2.*\.grib2\)".*/\1/' | tail -1 | cut -d_ -f1`
    lasts+=(${last})
done

export lastAvailDateTime=`printf '%s\n' "${lasts[@]}"|sort | tail -1`
lastDlDateTime=`cat ${MAIN}/.lastDlDateTime`

if [[ -e ${MAIN}/.active ]] || [[ ${lastAvailDateTime} == ${lastDlDateTime} ]] || [[ -z ${lastAvailDateTime} ]] ; then
    exit
fi

touch ${MAIN}/.active
rm -r ${MAIN}/nc 2>/dev/null

export lastHour=`echo ${lastAvailDateTime} | sed 's/.*T\(.*\)Z/\1/'`

# rm -r ${MAIN}/grib2 2>/dev/null ##  DO NOT REMOVE.  IF DL FAILS DUE TO LACK OF FILES, WANT TO CONTINUE LATER.
mkdir ${MAIN}/grib2
cd ${MAIN}/grib2

# vars=(-WEonG_TMP_Sfc -WEonG_CONDARAIN_Sfc -WEonG_CONDASNOW_Sfc -WEonG_CONDICEP_Sfc -WEonG_GUST_Sfc -WEonG_WSPD_Sfc -WEonG_WDIR_Sfc -WEonG_DPT_Sfc _TCDC_Sfc _PRMSL_MSL _WEARN_Sfc _WEASN_Sfc -WEonG_CHARPCPN_Sfc -WEonG_DMNTPCPNTYPE_Sfc -WEonG_PCPNTYPE_Sfc -WEonG_SCNDPCPNTYPE_Sfc -WEonG_SKSTATE_Sfc -WEonG_TPCPNINTSTI_Sfc _RH_AGL-2m)
# vars=(-WEonG_TMP_Sfc -WEonG_GUST_Sfc -WEonG_WSPD_Sfc -WEonG_WDIR_Sfc -WEonG_DPT_Sfc _TCDC_Sfc _PRMSL_MSL _WEARN_Sfc _WEASN_Sfc -WEonG_CHARPCPN_Sfc -WEonG_DMNTPCPNTYPE_Sfc -WEonG_PCPNTYPE_Sfc -WEonG_SCNDPCPNTYPE_Sfc -WEonG_SKSTATE_Sfc -WEonG_TPCPNINTSTI_Sfc _RH_AGL-2m)
# vars=(-WEonG_PROBFZRA_Sfc -WEonG_PROBPL_Sfc -WEonG_CONDALPCPN_Sfc -WEonG_CONDASSN_Sfc -WEonG_CONDAPL_Sfc -WEonG_PROBRA_Sfc -WEonG_PROBSN_Sfc -WEonG_CONDAFZPCPN_Sfc -WEonG_DPT_Sfc -WEonG_GUST_Sfc -WEonG_HGTSNLVL_Sfc -WEonG_PROBLPCPN_Sfc -WEonG_PROBBLSN_Sfc -WEonG_PROBDZ_Sfc -WEonG_PROBFZDZ_Sfc -WEonG_PROBFZPCPN_Sfc -WEonG_PROBPCPN_Sfc -WEonG_CONDAPCPN_Sfc -WEonG_PROBSNSQ_Sfc -WEonG_TMP_Sfc -WEonG_PROBTSOCRNC_Sfc -WEonG_WDIR_Sfc -WEonG_WSPD_Sfc _TCDC_Sfc _PRMSL_MSL _RH_AGL-2m)
# vars=(-WEonG_TMP_Sfc -WEonG_CONDASSN_Sfc -WEonG_CONDALPCPN_Sfc -WEonG_WSPD_Sfc -WEonG_GUST_Sfc)
vars=(-WEonG_TMP_Sfc -WEonG_CONDASSN_Sfc -WEonG_CONDALPCPN_Sfc -WEonG_WSPD_Sfc -WEonG_DPT_Sfc)

export var
for var in ${vars[@]}; do
    parallel 'wget -nc ${dlLink}/${lastHour}/{}/${lastAvailDateTime}_MSC_HRDPS${var}_RLatLon0.0225_PT{}H.grib2' ::: {001..048}
done

##  Only proceed if data is available for all 48 forecast hours
N=${#vars[@]}
for h in {001..048}; do
    n=$(ls ${lastAvailDateTime}*${h}H.grib2 | wc -l)
    if [[ $n -lt $N ]]; then
	rm ${MAIN}/.active
	echo "##  Not enough $h: $n<$N"
	exit 1
    fi
done

echo ${lastAvailDateTime} > ${MAIN}/.lastDlDateTime

cd ${MAIN}
sbatch job_HRDPS.sh
