#!/bin/bash

cd /Users/aponte/Cloud/Dropbox/Public/cswot_drifters

export mpg_dir="/home/lops/users/aponte/cswot_webpage"
scp dunree:$mpg_dir/cswot_large.mp4 .
scp dunree:$mpg_dir/cswot_south.mp4 .
scp dunree:$mpg_dir/cswot_central.mp4 .
scp dunree:$mpg_dir/cswot_north.mp4 .

