#!/bin/bash

model=HRDPS
export HERE=${HOME}/Projects/data/${model}
export remote=taimaz.ddns.net
export tiles=${remote}:/home/taimaz/models/${model}

fields=(temperature wind)


############################################################################
##  FUNCTIONS

function backJobs(){
    cd ${HERE}
    chk=1
    c=0
    while [[ ${chk} -ne 0 ]] && [[ $c -le 10 ]]; do
	for field in ${fields[@]}; do
    	    rsync -aurq --remove-source-files -e 'ssh -p 4412' ${HERE}/tiles/${field}/ ${tiles}/${field}/tiles
	done
	chk=`find ${HERE}/tiles -name *.png | wc -l`
	c=$((c+1))
    done

    ##  Update list of available dateTimes
    ssh -p 4412 ${remote} <<EOF
cd /home/taimaz/models/${model}
for d in */; do
if [[ -e /home/taimaz/models/${model}/\$d/tiles ]]; then
cd /home/taimaz/models/${model}/\$d/tiles
ls -d ${model}* | cut -d_ -f3- > .availDateTimes
fi
done
EOF

    rm -r ${HERE}/tiles
}

##  FUNCTIONS
############################################################################


rm -r ${HERE}/tiles

for field in ${fields[@]}; do
    cd ${HERE}/nc/${field}
    for d in *; do
	cd ${HERE}/extracted/${field}/$d
	python3 ${HERE}/scripts/cnv.py ${HERE} `ls *_1015.nc | xargs -I{} basename {} .nc | cut -d_ -f1-4` ${field}
    done
done

##################################################
##  Remove empty tile directories
cd ${HERE}/tiles/
find . -type d -empty -delete


##################################################
##  Process and backup
backJobs &
