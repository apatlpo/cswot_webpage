import os, sys
from shutil import copyfile
from glob import glob

import numpy as np
import pandas as pd

from datetime import datetime
import urllib.request

import paramiko
from scp import SCPClient

from common import now, data_dir, load_keys, imeis

try:
    #from decode_iridium_novatech_class import NOVATECH
    import inovatech as inov
except:
    inov = None

# ------------------------------------- Carthe ----------------------------

def fetch_carthe(source, timestamp=True, verbose=True, alldata=True):
    """fetch drifter data from pacific gyre website"""

    # source: "lops", "cnr"

    label = "carthe_"+source

    url = load_keys()[label]
        
    if alldata:
        # 4 rows >= 20 min
        url = url.replace("&maxRowsEach=4", "")
    if timestamp:
        t = now()
        tstamp = "_" + t.strftime("%Y%m%d_%H%M%S")
    else:
        tstamp = ""
    file = os.path.join(data_dir, label + tstamp + ".csv")

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

# Coriolis data

coriolis_dir = "/home/datawork-coriolis-intranet-s/exp/co01/co0113/co011306/co01130601/co0113060101/imei"

def fetch_imeis_ssh():
    """ from imeis database fetch all txt files, via ssh
    """
    # connect to server via datarmor
    ssh, scp = connect_coriolis()

    # list available remote imeis
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(f"ls {coriolis_dir}")
    remote_imeis = [l.strip("\n") for l in ssh_stdout.readlines()]

    for k, k_imeis in imeis.items():
        for imei in k_imeis:
            print(f"Downloadling {k} / {imei}")
            
            # create local directory if not present
            local_dir = os.path.join(data_dir, "imeis", imei)        
            if not os.path.isdir(local_dir):
                os.mkdir(local_dir)
                
            # list local files
            local_files = glob(os.path.join(local_dir, "*.txt"))
            local_files_core = [f.split("/")[-1] for f in local_files]

            # list remote files
            if imei in remote_imeis:
                ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls "+os.path.join(coriolis_dir, imei, "ascii/*.txt"))
                remote_files = sorted([l.strip("\n") for l in ssh_stdout.readlines()])
                remote_files_core = [f.split("/")[-1] for f in remote_files]

                if len(remote_files)>0:
                    # find files that have not been copied
                    for rf, rp in zip(remote_files_core, remote_files):
                        if rf not in local_files_core:
                            scp.get(rp, local_path=os.path.join(local_dir, rf), preserve_times=True)
                            #print(f"Downloading {rf}")
                        else:
                            pass
                            #print(f"{rf} is already here")

    scp.close()
    ssh.close()

def fetch_imeis_local():
    """ from imeis database fetch all txt files, assumes coriolis disks are
    accessible
    """

    # list available remote imeis    
    remote_imeis = [i for i in os.listdir(coriolis_dir) if "300" in i]

    for k, k_imeis in imeis.items():
        for imei in k_imeis:
            print(f"Downloadling {k} / {imei}")
            
            # create local directory if not present
            local_dir = os.path.join(data_dir, "imeis", imei)        
            if not os.path.isdir(local_dir):
                os.mkdir(local_dir)
                
            # list local files
            local_files = glob(os.path.join(local_dir, "*.txt"))
            local_files_core = [f.split("/")[-1] for f in local_files]

            # list remote files
            if imei in remote_imeis:
                remote_files = glob(os.path.join(coriolis_dir, imei, "ascii/*.txt"))
                remote_files_core = [f.split("/")[-1] for f in remote_files]

                if len(remote_files)>0:
                    # find files that have not been copied
                    for rf, rp in zip(remote_files_core, remote_files):
                        if rf not in local_files_core:
                            copyfile(rp , os.path.join(local_dir, rf))
                            #print(f"Downloading {rf}")
                        else:
                            pass
                            #print(f"{rf} is already here")

def browse_imeis_local():
    """ from imeis database browse all txt files, assumes coriolis disks are
    accessible
    """

    # list available remote imeis    
    remote_imeis = [i for i in os.listdir(coriolis_dir) if "300" in i]

    for k, k_imeis in imeis.items():
        for imei in k_imeis:
            print(f"Browsing {k} / {imei}")
            
            # list remote files
            if imei in remote_imeis:
                remote_files = sorted(glob(os.path.join(coriolis_dir, imei, "ascii/*.txt")))
                remote_files_core = [f.split("/")[-1] for f in remote_files]

                if len(remote_files)>0:
                    # inspect last data file
                    f = remote_files[-1]
                    df = (pd.read_csv(f, parse_dates=["date"])
                        .rename(columns=dict(date="time", platform_code="id"))
                        .drop_duplicates()
                    )
                    df["time"] = df["time"].dt.tz_localize(None)
                    df = df.sort_values("time")
                    print(f)
                    print(df.iloc[-1]["time"])
                    #print(df[["time", "id", "longitude", "latitude"]].iloc[-1])

def connect_coriolis():
    """ open connection to datarmor, need pulse secure to be turned on"""

    # connect to datarmor
    ifr = load_keys()["ifremer"]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("datarmor", username=ifr["login"], password=ifr["password"])

    # create scp object
    scp = SCPClient(ssh.get_transport())
    #sftp = ssh.open_sftp()
    # SSHException: Channel closed.
    # https://stackoverflow.com/questions/28317347/python-paramiko-sshexception-channel-closed
    
    return ssh, scp

# ------------------------------------- .... ----------------------------

if __name__ == "__main__":

    # carthe: does not work with pulsesecure
    if "carthe" in sys.argv:
        print("Download Carthe drifters")
        if "all" in sys.argv:
            print("   ... all data")
            for s in ["lops", "cnr"]:
                fetch_carthe(s, timestamp=True, alldata=True) # once
        else:
            for s in ["lops", "cnr"]:
                fetch_carthe(s, timestamp=True, alldata=False)

    # svp
    #print("Download shom svp drifters")
    # manual download from gdrive

    # trefle
    #fetch_trefle()

    # imeis: requires pulsesecure
    if "imeis" in sys.argv:
        print("Download from imeis")
        if "ssh" in sys.argv:
            fetch_imeis_ssh()
        elif "browse" in sys.argv:
            browse_imeis_local()
        else:
            fetch_imeis_local()
