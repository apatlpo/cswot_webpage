# Generates an html page showing the trajectory of various instruments along with their position.

Checklist on dunree:

- download all carthe data once: `python download_carthe.py all`
- download all cmems data once: `python download_cmems.py`
- turn on crontab: 


The conda environment is described in the `environment.yml` file.

The html page is produced via a python script.

The script that launches the production of the html file is `job.zsh`. **editing required**

- Dropbox python: [1](https://stackoverflow.com/questions/23894221/upload-file-to-my-dropbox-from-python-script)
- Google drive python: [1](https://pythonhosted.org/PyDrive/index.html) [2]()
- [Pynsitu](https://pynsitu.readthedocs.io/en/latest/)

```
pip install PyDrive # gdrive
pip install cmemsapi # mercator data: https://help.marine.copernicus.eu/en/articles/4808073-how-to-download-a-large-volume-of-data-in-netcdf-or-csv-file-format#h_b058d12b93
```


`cmems-api` is a bit touchy to install

```
conda create --name cmems --channel conda-forge python=3.8 --yes
conda activate cmems
pip install cmemsapi
```


