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

# imeis of interest
imeis = dict(
    shom=[
        300534060015760,
        300534060211000, 
        300534062470440,
        300534062476700,
        300534060017440,
        300534060211410,
        300534062471390,
        300534062479690,
        300534060017750,
        300534060216070,
        300534062472380,
        300534062479710,
        300534060112360, 
        300534060218400,
        300534062472690,
        300534060113380,
        300534060315840,
        300534062472810,
        300534060114360,
        300534060316870,
        300534062474750,
        300534060011620,
        300534060116350,
        300534061170360,
        300534062475680,
        300534060012760,
        300534060117220,
        300534061175350,
        300534062475700,
    ],
    ogs = [
        300534064106800,
        300534064104920,
        300534064104890,
        300534064103920,
        300534064103890,
        300534064109890,
        300534064109870,
        300534064108950,
        300534064107900,
        300534064107880,
        300534060553240,
        300125061690570,   
    ],
    scripps = [
        300534061395960,
        300534061395970,
        300534061395980,
        300534061398320,
        300534061398370,
        300534061398910,
        300534064300460,
        300534064300510,
    ],
    bgc = [
        300534061492130,
    ],
)
# converts imeis to strings
for k, v in imeis.items():
    imeis[k] = [str(i) for i in v]

shom_tmp = [
 '300534062472690',
 '300534062475680',
 '300534062472380',
 '300534062470440',
 '300534062479690',
 '300534062472810',
 '300534062476700',
 '300534060017350',
 '300534062479710',
 '300534062478740',
 '300534062478470',
 '300534062474750',
 '300534062471390',
 '300534060117220',
 '300534060011620',
 '300534060212000',
 '300534060211000',
 '300534061170360',
 '300534061175350',
 '300534060017440',
 '300534060211410',
 '300534060218400',
 '300534060316870',
 '300534060015760',
 '300534060315840',
 '300534060216070',
 '300534060014780',
 '300534060114360',
 '300534060012760',
 '300534060354800',
 '300534060112360',
 '300534060116350',
 '300534060113380',
 '300534060017750',
 '300534062475700',
 '300534060315850',
]

# --------------------------- utils ----------------------------------------------

def load_keys():
    with open("keys/keys.yaml", "r") as stream:
        try:
            keys = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return keys

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

def load_carthe(source, last=False, file=None):
    """Load drifter data into a dict of dataframes"""
    label = "carthe_"+source
    if last:
        drifter_files = [find_latest_drifter_file(label)]
    elif file is not None:
        drifter_files = [file]
    else:
        drifter_files = glob(os.path.join(data_dir, label+"*.csv"))
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

# ------------------------------------- from imeis ----------------------------

def load_imei(imei):
    """ load all files associated with one imei """
    local_dir = os.path.join(data_dir, "imeis", imei)
    files = sorted(glob(os.path.join(local_dir, imei+"*.txt")))
    #files = sorted(glob(os.path.join(local_dir, "*.txt")))
    # clean up
    #clean=True
    #if clean:
    #    files_gd = sorted(glob(os.path.join(local_dir, imei+"*.txt")))
    #    for f in files:
    #        if f not in files_gd:
    #            os.remove(f)
    #    files = files_gd
    if not files:
        return None
    df = (pd.concat([pd.read_csv(f, parse_dates=["date"]) for f in files], axis=0)
          .rename(columns=dict(date="time", platform_code="id"))
          .set_index("id")
          .drop_duplicates()
    )
    df["time"] = df["time"].dt.tz_localize(None)
    return df

def load_imeis(imeis):
    """ load a list of emails and concatenate data into a single dataframe """
    print(f"  loading {len(imeis)} imeis")
    D = [load_imei(i) for i in imeis]
    D = [d for d in D if d is not None]
    if not D:
        return None
    df = pd.concat(D, axis=0)
    # filter out old or bad data
    df = df.loc[ df.time>pd.Timestamp('2023-03-28 09:00') ]
    df = df.loc[ (df.latitude<45.) | (df.longitude>0.) ]
    return df

# ------------------------------------- dropbox ----------------------------

#def push_dropbox():   
#   dbx = dropbox.Dropbox(self.access_token)


# ------------------------------------- swot tracks ------------------------------

from shapely.geometry import Polygon
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# path to swot tracks
#tracks_dir = "/Users/aponte/Data/swot"
tracks_dir = "/home/datawork-lops-osi/equinox/misc/swot"

def load_swot_tracks(phase="calval", resolution=None, bbox=None, **kwargs):
    """Load SWOT tracks

    Parameters
    ----------
    phase: str, optional
        "calval" or "science"
    resolution: str, optional
        Specify resolution, for example "10s", default is "30s"
    """
    
    #
    files = glob(os.path.join(tracks_dir, "*.shp"))
    files = [f for f in files if phase in f]
    if resolution is not None:
        files = [f for f in files if resolution in f]
    dfiles = {f.split("_")[-1].split(".")[0]: f for f in files}
    out = {key: gpd.read_file(f, **kwargs) for key, f in dfiles.items()}

    if bbox is None:
        return out

    central_lon = (bbox[0] + bbox[1]) * 0.5
    central_lat = (bbox[2] + bbox[3]) * 0.5

    polygon = Polygon(
        [
            (bbox[0], bbox[2]),
            (bbox[1], bbox[2]),
            (bbox[1], bbox[3]),
            (bbox[0], bbox[3]),
            (bbox[0], bbox[2]),
        ]
    )
    out = {key: gpd.clip(gdf, polygon) for key, gdf in out.items()}

    return out


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
    tracks = load_swot_tracks()
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
            ax.plot(_df.longitude, _df.latitude, color="0.8", transform=crs, zorder=2)
            _df = _df.loc[t-pd.Timedelta(trail):]
            H[drlabel].append(ax.plot(_df.longitude, _df.latitude, **dr[1], transform=crs, zorder=3))
            #
            if not _df.empty:
                ax.scatter(_df.iloc[-1].longitude, _df.iloc[-1].latitude, 
                           s=20, marker="o", color="k",
                           transform=crs,
                           zorder=4,
                          )

    ax.legend([h[0][0] for label, h in H.items()], [label for label, h in H.items()])
    ax.set_title(t.strftime("%H:%M %d/%m/%Y"))

    if savefig is not None:
        fig.savefig(savefig)
        