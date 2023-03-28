import numpy as np
import pandas as pd

from datetime import datetime

# data repository
#data_dir = "./data"
data_dir = "/home/datawork-lops-osi/aponte/cswot"

deg2rad = np.pi/180
now = lambda: pd.to_datetime(datetime.utcnow())

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

