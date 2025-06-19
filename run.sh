#!/bin/bash
source ./configs.sh

##########################################################################
## CHECK LAST DL DATE TIME vs. AVAILABLE DATE TIME
export dlLink="https://dd.weather.gc.ca/model_hrdps/continental/2.5km"
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

##########################################################################


export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)

docker run --user ${LOCAL_UID}:${LOCAL_GID} --rm -v /tmp:/app/data -e lastAvailDateTime=${lastAvailDateTime} hrdps:latest
if [[ $? -ne 0 ]]; then
    echo "##  Docker run failed"
    rm ${MAIN}/.active
    exit 1
fi


cd /tmp/${MODEL}_nc
for d in *; do
    cd /tmp/${MODEL}_nc/${d}
    rm *.nc
    mv data/cities.json .
    mv images/* .
    rm -r data images
done
rsync -aru /tmp/${MODEL}_nc/ ${SERVER_IP}:${SERVER_DIR}/ || exit 1
# rsync -aru /tmp/${MODEL}_nc/ ${SERVER_DIR}/

cd ${MAIN}
rm -r /tmp/${MODEL}_grib2 /tmp/${MODEL}_nc

echo ${lastAvailDateTime} > .lastDlDateTime
rm .active
