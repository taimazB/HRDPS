docker build -t hrdps:latest .
docker save hrdps:latest | gzip > hrdps.tar.gz
