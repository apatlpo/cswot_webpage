#!/bin/zsh

# load conda environment

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/Users/aponte/.miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/Users/aponte/.miniconda3/etc/profile.d/conda.sh" ]; then
        . "/Users/aponte/.miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/Users/aponte/.miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

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


