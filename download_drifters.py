import os
from glob import glob

import numpy as np
import pandas as pd

from datetime import datetime
import urllib.request

from common import now, data_dir

# ------------------------------------- Carthe ----------------------------

def fetch_carthe(timestamp=True, verbose=True, alldata=True):
    """fetch drifter data from pacific gyre website"""

    with open("keys/carthe", "r") as f:
        # do things with your file
        url = f.read().strip()
    if alldata:
        # 4 rows >= 20 min
        url = url.replace("&maxRowsEach=4", "")
    if timestamp:
        t = now()
        tstamp = "_" + t.strftime("%Y%m%d_%H%M%S")
    else:
        tstamp = ""
    file = os.path.join(data_dir, "carthe" + tstamp + ".csv")

    urllib.request.urlretrieve(url, file)

    if verbose:
        print(f" Drifter data downloaded as {file}")

    return file


# ------------------------------------- .... ----------------------------

if __name__ == "__main__":

    import sys
    if len(sys.argv)>1 and "all" in sys.argv:
        print("Downloading all data")
        fetch_carthe(timestamp=True, alldata=True) # once
    else:
        fetch_carthe(timestamp=True, alldata=False)
