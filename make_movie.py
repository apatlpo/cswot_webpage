import os

import pandas as pd
import matplotlib.pyplot as plt

import common as co

### load data

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
svp = co.load_svp_shom()

# trefle
trefle = co.load_trefle()

# cmems
#chl = co.load_cmems(V="chl")["CHL"]
#adt = co.load_cmems(V="ssh")["adt"]

# https://boundingbox.klokantech.com

extents = dict(
    large=[2.9, 6.74, 39.54, 43.55],
    south=[3.5, 5.5, 40, 41],
    central=[4., 6, 41, 42],
    north=[4.5, 6.5, 42, 43.2],
)

lw=3
drifters = dict(carthe=[ca, dict(color="gold", lw=lw)],
                svp=[svp, dict(color="royalblue", lw=lw)],
                trefle=[trefle, dict(color="forestgreen", lw=lw)]
               )

#e = "large"
#e = "south"
#e = "central"
#e = "north"

#for e in ["south", "central", "north"]:
for e in ["large", "south", "central", "north"]:

    t = pd.Timestamp('2023-03-28 09:00') # first carthe deployment
    dt = pd.Timedelta("1H")
    #end = pd.to_datetime(datetime.datetime.now()).ceil(dt)
    end = max([d[0].time.max() for _, d in drifters.items()]).ceil(dt)
    trail = "34H"

    # clean up folder
    print_dir = "/Users/aponte/tmp/figs_"+e
    co.delete_folder(print_dir)

    i = 0
    with plt.ioff():
        while t<=end:
            co.plot_trails(t, extents[e], drifters, trail="5D", 
                           savefig=os.path.join(print_dir, f"{i:04d}.png"),
                           )
            t+=dt
            i+=1


