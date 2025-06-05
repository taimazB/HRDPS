MODEL=hrdps
docker build -t ${MODEL}:latest .
docker save ${MODEL}:latest | gzip > ${MODEL}.tar.gz
