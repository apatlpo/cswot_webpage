#!/bin/bash

echo "-------------------------"
date

# load conda
source /home/lops/users/aponte/.miniconda3/etc/profile.d/conda.sh

cd /home/lops/users/aponte/cswot_webpage

# update cmems data
conda activate cmems
python download_cmems.py

# update drifter data
conda activate pynsitu
python download_carthe.py

# create html
#python generate_html.py

# send html to dropbox / gdrive

date

