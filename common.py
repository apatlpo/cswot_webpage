import os, shutil
from glob import glob
import yaml

import numpy as np
import xarray as xr
import pandas as pd

from datetime import datetime

try:
    import pynsitu as pin
    crs = pin.maps.crs
except:
    pin, crs = (None,)*2

# data repository
data_dir = "./data"
#data_dir = "/home/datawork-lops-osi/aponte/cswot"

deg2rad = np.pi/180
now = lambda: pd.to_datetime(datetime.utcnow())

def load_keys():
    with open("keys/keys.yaml", "r") as stream:
        try:
            keys = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return keys

# --------------------------- utils ----------------------------------------------

def delete_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

# --------------------------- synthetic data -------------------------------------

def generate_one_trajectory(u_mean=0, v_mean=0, u_wave=0, noise=0, id=0, lon=4, lat=41):

    freq = "1H"

    time_unit = pd.Timedelta("1s")
    dt = pd.Timedelta(freq) / time_unit
    time = pd.date_range(start="2018-01-01", end="2018-01-15", freq=freq)
    _time = (time - time[0]) / time_unit

    #lon0, lat0 = -20, 30
    #lon0, lat0 = 4, 41
    scale_lat = 111e3
    scale_lon = scale_lat * np.cos(lat * deg2rad)
    
    T = pd.Timedelta("1D") / time_unit

    u = (
        u_mean
        + u_wave * np.cos(2 * np.pi * _time / T)
        + np.random.randn(time.size) * noise
    )
    v = (
        v_mean
        + u_wave * np.sin(2 * np.pi * _time / T)
        + np.random.randn(time.size) * noise
    )

    lon = lon + np.cumsum(u) * dt / scale_lon
    lat = lat + np.cumsum(v) * dt / scale_lat

    df = pd.DataFrame(dict(lon=lon, lat=lat, time=time))
    df["id"] = id
    df = df.set_index("time")

    return df


# ------------------------------------- cmems ----------------------------

def load_cmems(V=None, last=False):
    """Load cmems data"""
    if V is None:
        V = ["ssh", "chl", "sst"]
    if isinstance(V, list):
        return xr.merge([load_cmems(V=v, last=last) for v in V])
    assert isinstance(V, str), "V is not a string" 

    files = sorted(glob(os.path.join(data_dir, f"cmems_{V}_*.nc")))

    ds = xr.concat([xr.open_dataset(f) for f in files], "time")
    
    return ds

# ------------------------------------- carthe ----------------------------

def load_carthe(last=False, file=None):
    """Load drifter data into a dict of dataframes"""
    if last:
        drifter_files = [find_latest_drifter_file("carthe")]
    elif file is not None:
        drifter_files = [file]
    else:
        drifter_files = glob(os.path.join(data_dir, "carthe*.csv"))
    df = (pd.concat([pd.read_csv(f, parse_dates=["DeviceDateTime"])
                    for f in drifter_files])
          .drop_duplicates()
          .sort_index()
         )
    df = df.rename(columns=dict(CommId="id", Longitude="longitude", Latitude="latitude", DeviceDateTime="time"))
    
    return df.set_index("id")

def find_latest_drifter_file(suffix):
    """find latest drifter file"""
    #local_dir = os.getcwd()
    drifter_files = glob(os.path.join(data_dir, suffix+"*.csv"))
    if len(drifter_files)==0:
        return None
    mtimes = [os.path.getmtime(f) for f in drifter_files]
    latest_file = drifter_files[mtimes.index(max(mtimes))]
    return latest_file

# ------------------------------------- svp ----------------------------

def load_file_svp_shom(file):
    """ read one shom svp file """

    # get id
    dr_id = int(file.split("_")[-1].split(".")[0])
    
    with open(file, encoding="unicode_escape") as f:
        d = list(f.readlines())

    # replace NUL, strip whitespace from the end of the strings, split each string into a list
    d = [v.replace("\n", "").split() for v in d]

    d = [[pd.Timestamp(l[0]+" "+l[1]),]+[float(v) for v in l[2:]] for l in d]

    df = pd.DataFrame(d, columns=["time", "latitude", "longitude", "temperature"]).set_index("time")
    df["id"] = dr_id

    return df

def load_svp_shom(svp_root_dir = "data/svp_shom/"):
    """ read all shom svp files"""
    
    # select last dir
    #dirs = sorted(glob(os.path.join(svp_root_dir, "2023*")))
    #svp_dir = "202304030500"
    
    #svp_dir = dirs[-1]
    #print(dirs, " selected : ", svp_dir)

    svp_files = glob(os.path.join(svp_root_dir, "decod_*.txt"))
    df = pd.concat([load_file_svp_shom(file) for file in svp_files])
    df = df.reset_index().set_index("id")
    
    return df
    

# ------------------------------------- trefle ----------------------------

def load_trefle():

    import inovatech as inov

    ntech = inov.NOVATECH(data_dir)

    df = ntech.load_all_positions(300434064301970)
    df = df.rename(columns=dict(lon="longitude", lat="latitude"))
    df = df.geo.compute_velocities()
    #.rename(columns=dict(IMEI="id"))
    df["id"] = "trefle"
    df = df.reset_index().set_index("id")
    
    return df


# ------------------------------------- dropbox ----------------------------

#def push_dropbox():   
#   dbx = dropbox.Dropbox(self.access_token)


# ------------------------------------- swot tracks ------------------------------

try:
    from mitequinox.utils import load_swot_tracks
    from shapely.geometry import Polygon
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs

    tracks = load_swot_tracks()
except:
    tracks = None

def plot_swot_tracks(bbox, ax=None, figsize=(10,10), fig=None, **kwargs):

    central_lon = (bbox[0]+bbox[1])*0.5
    central_lat = (bbox[2]+bbox[3])*0.5

    polygon = Polygon([(bbox[0], bbox[2]), 
                       (bbox[1], bbox[2]), 
                       (bbox[1], bbox[3]), 
                       (bbox[0], bbox[3]), 
                       (bbox[0], bbox[2]),
                      ])
    #poly_gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs=world.crs)
    gdf = tracks["swath"]
    gdf_clipped = gpd.clip(gdf, polygon)

    if ax is None:
        #crs = ccrs.Orthographic(central_lon, central_lat)
        crs = ccrs.AlbersEqualArea(central_lon, central_lat)
        fig, ax = plt.subplots(1, 1, 
                               subplot_kw={'projection': crs},
                               figsize=figsize,
                              )
        ax.set_extent(bbox)
    else:
        crs = ax.projection
        
    crs_proj4 = crs.proj4_init

    #_gdf = gdf.cx[bbox[0]:bbox[1], bbox[2]:bbox[3]]
    _gdf = gdf_clipped
    gdf_crs = _gdf.to_crs(crs_proj4)
    dkwargs = dict(facecolor='0.9', edgecolor='0.5', alpha=0.5)
    dkwargs.update(**kwargs)
    ax.add_geometries(gdf_crs['geometry'],
                      crs=crs,
                      **dkwargs
                     )

    if fig is not None:
        ax.gridlines(draw_labels=True)
        ax.coastlines(resolution='50m')
        return fig, ax
    else:
        return ax
    

# ------------------------------------- drifter plotting ------------------------------

def plot_trails(t, e, drifters, trail="5D", savefig=None, figsize=(7,7)):

    fig, ax, _ = pin.maps.plot_map(extent=e, land="10m", coastline="10m", figsize=figsize)

    plot_swot_tracks(e, ax=ax)

    H = dict()
    for drlabel, dr in drifters.items():
        _dr = dr[0].reset_index().set_index("id")
        ids = _dr.index.unique()
        H[drlabel] = []
        for i in ids:
            _df = (_dr.loc[i]
                   .set_index("time").sort_index()
                   .loc[:t]
            )
            # trail
            ax.plot(_df.longitude, _df.latitude, color="0.8", transform=crs)
            _df = _df.loc[t-pd.Timedelta(trail):]
            H[drlabel].append(ax.plot(_df.longitude, _df.latitude, **dr[1], transform=crs))            
            #
            if not _df.empty:
                ax.scatter(_df.iloc[-1].longitude, _df.iloc[-1].latitude, 
                           s=30, marker="x", color="k",
                           transform=crs,
                          )

    ax.legend([h[0][0] for label, h in H.items()], [label for label, h in H.items()])
    ax.set_title(t.strftime("%H:%M %d/%m/%Y"))

    if savefig is not None:
        fig.savefig(savefig)
        