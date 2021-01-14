# Hidrodata_ARGENTINA
Download the hydrological data from Argentina.

## Installation
Create an environment to use the package : 

```bash
conda create -n HidroARG -c conda-forge netcdf4 geckodriver selenium pandas cartopy openpyxl
```
Activate the environment to run the script : 

``` bash
conda activate HidroARG
```
To run the example, go into the example folder and then : 
``` bash
python caudal_media_mensual.py
```

Deactivate the environment when you are done : 
``` bash
conda deactivate
```

## Get the shapefile from WMO / GRDC
Open the terminal an go to the shapefile repertory, then : 
``` bash
bash get_shp.bash
```

## Content

* **Example/**
  * caudal_media_mensual.py : example to download the monthly mean discharge over all the stations from the "Red Hidrologica Nacional"
* **lib/**
  * download.py : functions to download the metadata and the discharge data
  * export_netcdf.py : export the discharge in an adequate netCDF format. (for now it requires the original netCDF example file) 
  * get_WMO.py : get the WMO region and subregion that are used in GRDC
* **shapefile/**
  * get_shp.bash : get the shapefile from WMO / GRDC

## Acknowledgements
Sistema Nacional de Información Hídrica


