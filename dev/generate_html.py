import os
from glob import glob

import numpy as np
import pandas as pd
import xarray as xr

import hvplot.pandas  # noqa
import hvplot.xarray  # noqa

import panel as pn
import holoviews as hv

hv.extension('bokeh')
pn.extension(sizing_mode="stretch_width")

import cartopy.crs as ccrs

import pynsitu as pin
import common as co



if __name__ == "__main__":

    # load data
    ca = load_carthe()
    # svp shom
    # ...
    # trefle
    trefle = load_trefle()
    # svp italy
    # ...
    # carthe italy

    # generate figure and store as html

    # push html file to dropbox and google drive
    # push_dropbox()
    # push_gdrive()





