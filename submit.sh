#!/bin/bash
#SBATCH --job-name=HRDPS
#SBATCH --nodes=1
#SBATCH --cpus-per-task=32
#SBATCH --time=12:00:00
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
#SBATCH --priority=2001

export MAIN=$PWD
export SERVER_IP=taimaz.ddns.net
# export SERVER_PORT=22
export SERVER_DIR=/home/taimaz/Projects/Blender/Projects/weather

##  This file is included in the docker image for reference only.
data
docker run --rm -v ./:/app hrdps:latest
data

rsync -ar --exclude '*.nc' --delete ${MAIN}/nc ${SERVER_IP}:${SERVER_DIR}

rm .active
