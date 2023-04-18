import os
from glob import glob
import yaml

import numpy as np
import pandas as pd

from datetime import datetime
import urllib.request

from common import now, data_dir, load_keys
#from decode_iridium_novatech_class import NOVATECH
import inovatech as inov

# ------------------------------------- Carthe ----------------------------

def fetch_carthe(timestamp=True, verbose=True, alldata=True):
    """fetch drifter data from pacific gyre website"""

    url = load_keys()["carthe"]
        
    if alldata:
        # 4 rows >= 20 min
        url = url.replace("&maxRowsEach=4", "")
    if timestamp:
        t = now()
        tstamp = "_" + t.strftime("%Y%m%d_%H%M%S")
    else:
        tstamp = ""
    file = os.path.join(data_dir, "carthe" + tstamp + ".csv")

    print(url)
    print(file)
    urllib.request.urlretrieve(url, file)

    if verbose:
        print(f" Drifter data downloaded as {file}")

    return file

def fetch_trefle():
    """ fetch novatech iridium data """
    # create novatech object
    ntech = inov.NOVATECH(data_dir)
    # load emails
    email = load_keys()["email"] # read credentials
    ntech.Read_Ifremer_Inbox_mail(email["login"], email["password"])


# ------------------------------------- .... ----------------------------

if __name__ == "__main__":

    # carthe
    import sys
    if len(sys.argv)>1 and "all" in sys.argv:
        print("Downloading all data")
        fetch_carthe(timestamp=True, alldata=True) # once
    else:
        fetch_carthe(timestamp=True, alldata=False)

    # svp
    # manual download from gdrive

    # trefle
    fetch_trefle()
