# Define the base image
FROM ubuntu:24.04

ENV MODEL=HRDPS

# Update package lists
RUN apt-get update && apt-get upgrade -y

# Install Python 3.12.3 and dependencies
RUN apt-get install -y \
  wget \
  cdo=2.4.0-1build3 \
  parallel \
  rsync \
  nco=5.2.1-1build2 \
  python3-imageio \
  python3-shapely \
  python3-geopy

# RUN curl -sL https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz | tar -xzf - --strip-components=1

# Set the working directory
WORKDIR /app

# Copy your application code here
COPY . .

# Define the command to run
CMD [ "bash", "dl_HRDPS.sh" ]
