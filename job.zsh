#!/bin/zsh

# load and activate conda environment
source /home/lops/users/aponte/.miniconda3/etc/profile.d/conda.sh
conda activate pynsitu

# move to work directory
cd /home/lops/users/aponte/cswot_webpage

# download drifter data
rm data/carthe_*.csv
python download_drifters.py carthe all imeis


# make movie
rm *.mp4
python make_movie.py

# temporary: converts notebook to python script
#jupyter nbconvert --to python generate_html.ipynb

# execute script
#python generate_html.py 


