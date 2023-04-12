import os
from glob import glob
import yaml

import pandas as pd

#from ftplib import FTP
#from datetime import datetime,timedelta

from common import now, data_dir, load_keys

def download_variable(variable, start=None, end=None):
    """ load one variables """

    if end is None:
        end = now()
    if start is None:
        start = now()

    # loop around days
    if end-start>pd.Timedelta("1D"):
        t = start
        dt = pd.Timedelta("1D")
        files_out = []
        while t<end:
            files_out.append(download_variable(variable, start=t, end=t))
            t+=dt
        return files_out

    start = str(start.floor("1D"))
    end = str(end.floor("1D")).replace("00:00:00", "23:59:59")

    #coms = load_cmems_commands()
    coms = load_keys()["cmems"]

    file_out = 'cmems_'+variable+'_'+start[0:10]+'.nc'

    print(start, end, file_out)
    #return file_out
    if not os.path.isfile(os.path.join(data_dir, file_out)):
        query = (coms[variable].replace('DATE_START', start)
                .replace('DATE_END', end)
                .replace('OUT_DIR', data_dir)
                .replace('CMEMS_DATE.nc', file_out)
                )
        os.system(query)
    
    return file_out


if __name__ == "__main__":

    variables = ["ssh", "chl", "sst"]
    start=pd.Timestamp("2023/03/15")
    #variable = "chl"

    for v in variables:
        download_variable(v, start=start)







