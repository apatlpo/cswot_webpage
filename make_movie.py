import os
import sys

import pandas as pd
import matplotlib.pyplot as plt

import common as co

print_dir_root = "/Users/aponte/tmp/"

# https://boundingbox.klokantech.com
extents = dict(
    large=[2.9, 6.74, 39.54, 43.55],
    south=[3.5, 5.5, 40, 41],
    central=[4., 6, 41, 42],
    north=[4.5, 6.5, 42, 43.2],
)

### load data
overwrite=False
if "overwrite" in sys.argv:
    overwrite=True
    print("Overwrites existing figures")


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

#e = "large"
#e = "south"
#e = "central"
#e = "north"

#for e in ["south", "central", "north"]:
for e in ["large", "south", "central", "north"]:

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
        #while i<=5: # dev !
        while t<=end:
            savefig = os.path.join(print_dir, f"{i:04d}.png")
            if not overwrite and os.path.isfile(savefig):
                print(t, "  ... passing")
            else:
                print(t, "  printing")
                co.plot_trails(t, extents[e], drifters, 
                            trail=trail, 
                            savefig=savefig,
                            )
            t+=dt
            i+=1


