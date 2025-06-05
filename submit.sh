#!/bin/bash
#SBATCH --job-name=HRDPS
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --time=12:00:00
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
#SBATCH --priority=2001

##  This file is included in the docker image for reference only.

export MAIN=$PWD
export SERVER_IP=taimaz.ddns.net
export SERVER_DIR=/home/taimaz/Projects/Blender/Projects/sialuk/data/models/

export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)

docker run --user ${LOCAL_UID}:${LOCAL_GID} --rm -v ./:/app hrdps:latest

cd ${MAIN}/nc
ls | parallel 'rsync -au {}/images/ ${SERVER_IP}:${SERVER_DIR}/{}/'

cd ${MAIN}
rm -r ${MAIN}/grib2 ${MAIN}/nc

rm .active
