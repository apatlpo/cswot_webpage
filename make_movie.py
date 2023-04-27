import os, sys
from subprocess import check_output, STDOUT
from glob import glob

import dropbox

import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime

import common as co

#print_dir_root = "/Users/aponte/tmp/"
print_dir_root = "./"

# https://boundingbox.klokantech.com
extents = dict(
    large=[2.9, 6.74, 39.54, 43.55],
    south=[3.5, 5.5, 40, 41],
    central=[4., 6, 41, 42],
    north=[4.5, 6.5, 42, 43.2],
)
<<<<<<< Updated upstream
regions = list(extents)

def print_figs(overwrite):
    """ print figures """

    ### load data
    print("Load data - start")

    # carthe
    ca = co.load_carthe()
    # add velocity
    ca = (ca
        .groupby("id").apply(lambda df: df.set_index("time").geo.compute_velocities())
        .reset_index()
        )
    # manually get rid of early data
    ca = ca.loc[ca.time>pd.Timestamp("2023/03/27")].set_index("id")

    # shom svp
    #svp = co.load_svp_shom()

    # trefle
    trefle = co.load_trefle()

    # from imeis
    shom = co.load_imeis(co.imeis["shom"])
    ogs = co.load_imeis(co.imeis["ogs"])
    scripps = co.load_imeis(co.imeis["scripps"])
    bgc = co.load_imeis(co.imeis["bgc"])

    # cmems
    #chl = co.load_cmems(V="chl")["CHL"]
    #adt = co.load_cmems(V="ssh")["adt"]

    print("Load data - end")

    lw=2
    drifters = dict(carthe=[ca, dict(color="gold", lw=lw)],
                    trefle=[trefle, dict(color="forestgreen", lw=lw)],
                    shom=[shom, dict(color="royalblue", lw=lw)],
                    ogs=[ogs, dict(color="orange", lw=lw)],
                    scripps=[scripps, dict(color="cadetblue", lw=lw)],
                    bgc=[bgc, dict(color="coral", lw=lw)],
                )
    # filter out empty fields
    drifters = {k: v for k, v in drifters.items() if v[0] is not None}

    t0 = pd.Timestamp('2023-03-28 09:00') # first carthe deployment
    #t0 = pd.Timestamp('2023-04-10 09:00') # dev !
    #dt = pd.Timedelta("30M")
    dt = pd.Timedelta("1H")
    trail = "34H"
    now = pd.to_datetime(datetime.now()).ceil(dt)
    now_minus_24h = now - pd.Timedelta("24h")

    i_start = dict(large=0, south=190, central=80, north=0)

    #for e in ["south", "central", "north"]:
    for e in regions:

        print(f"Start processing region {e}")

        t = t0
        #end = pd.to_datetime(datetime.datetime.now()).ceil(dt)
        end = max([d[0].time.max() for _, d in drifters.items()]).ceil(dt)

        # clean up folder
        print_dir = os.path.join(print_dir_root, "figs_"+e)
        if not os.path.isdir(print_dir):
                    os.mkdir(print_dir)
        if overwrite:
            co.delete_folder(print_dir)

        i = 0
        with plt.ioff():
            # skips some time steps
            while i<i_start[e]:
                t+=dt
                i+=1
            #while i<=5: # dev !
            while t<=end:
                savefig = os.path.join(print_dir, f"{i:04d}.png")
                if not overwrite and os.path.isfile(savefig) and t<now_minus_24h:
                    print(t, "  ... passing")
                else:
                    print(t, "  printing")
                    co.plot_trails(t, extents[e], drifters, 
                                trail=trail, 
                                savefig=savefig,
                                )
                t+=dt
                i+=1

def generate_mpg():
    """ generate mpg files """

    for e in regions:
        
        print_dir = os.path.join(print_dir_root, "figs_"+e)

        # generate movies, requires ffmpeg in environment, do with image2Movies otherwise
        # https://stackoverflow.com/questions/24961127/how-to-create-a-video-from-images-with-ffmpeg
        com = f'''ffmpeg -framerate 10 -pattern_type glob -i '{print_dir}/*.png' -c:v libx264 -pix_fmt yuv420p cswot_{e}.mp4'''
        output = check_output(com, shell=True, stderr=STDOUT, universal_newlines=True).rstrip('\n')
        #print(output)
        print(f"movies should be ready: cswot_{e}.mp4'")

def push_dropbox():
    """ push to dropbox """

    mpg = sorted(glob("*.mp4"))

    # https://www.dropbox.com/developers/documentation/python#tutorial
    token = co.load_keys()["dropbox"]["token"]
    dbx = dropbox.Dropbox(token)
    #for entry in dbx.files_list_folder('Public/cswot_drifters').entries:
    #    print(entry.name)

    mode = dropbox.files.WriteMode.overwrite
    #data = b"Potential headline: Game 5 a nail-biter as Warriors inch out Cavs"
    for f in mpg:
        with open(f, 'rb') as fo:
            data = fo.read()
        dbx.files_upload(data, '/Public/cswot_drifters/'+f.split("/")[-1], mode)

if __name__=="__main__":
     
    overwrite=False
    if "overwrite" in sys.argv:
        overwrite=True
        print("Overwrites existing figures")

    if not "nofigs" in sys.argv:
         print_figs(overwrite)

    generate_mpg()

    push_dropbox()

