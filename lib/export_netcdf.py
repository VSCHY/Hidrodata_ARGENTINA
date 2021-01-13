import glob
import pandas as pd
import re
import os
import datetime
import numpy as np
from netCDF4 import Dataset, stringtochar
from netCDF4 import num2date, date2num
from datetime import datetime
import unicodedata
import sys
from get_WMO import WMOREG
#
dfile = "../shapefile/wmobb_basins.shp"
#../../WMO_basins/Originals/wmo_basins_shp/wmobb_basins.shp
if not os.path.exists(dfile):
    print("Please enter a valid direction for wmobb_basins.shp")
    print("Can be downloaded from ftp://ftp.bafg.de/pub/REFERATE/GRDC/wmo_basins_shp.zip")
    sys.exit()

    
WMO = WMOREG(dfile)

############################

def getdfmeta(dmetafile):
   # Metadata
   dfmeta = pd.read_csv(dmetafile, sep = ";")
   dfmeta.index = dfmeta["Codigo"]
   return dfmeta
   #
L_varstr = ["river", "name", "LastUpdate", "FileDate"]
L_varfloat = ["altitude","area","lat","lon"]

def txt_without_accent(text):
    txt_out = text.replace(" ", "_")
    txt_out = unicodedata.normalize('NFD', txt_out).encode('ascii', 'ignore')
    txt_out = txt_out.decode('utf-8')
    #txt_out = text.replace("_", " ")
    return txt_out

def get_info_st(A):
    D = {}
    print(A.loc['Lugar'])#.values
    D["name"] = txt_without_accent(A.loc['Lugar']).replace("_"," ")
    D["altitude"] = np.nan
    D["river"] = txt_without_accent(A.loc['Rio']).replace("_"," ")
    D["area"] = A.loc['Area']
    D["lat"] = -1*A.loc['Latitud']
    D["lon"] = -1*A.loc['Longitud']
    D["country"] = "AR"
    D["LastUpdate"] = str.encode(A.loc["Registro"][:10])
    D["FileDate"] = "06-01-2021"
    return D

def get_data(d, dfmeta):
   # INDEX of the station to get Metadata
   num = int(d.split("/")[-1].replace("Historicos-Estacion ", "").replace(".xlsx",""))
   A = dfmeta.loc[num+10000]
   #
   #
   df = pd.read_excel(d, skiprows = 1, header = 0, engine='openpyxl')
   c = df.columns[-1]
   # In the the river is dry, it's 0 Rio Seco, we have to remove this
   df[c] = df[c].apply(lambda x: str(x).replace(" Río Seco",""))
   # Remove "dudoso"
   df = df[~df["Caudal Medio Mensual [m3/seg]"].str.contains("Dudoso")]
   # Convert the data to float
   df[c] = df[c].astype(float)
   #
   # Handling time
   dtindex = pd.to_datetime(df["Fecha y Hora"], format = '%d/%m/%Y %H:%M') 
   #dtindex = pd.DatetimeIndex(df["Fecha y Hora"])#.strftime("%m/%d/%Y")
   df['date'] = pd.to_datetime(dtindex)  + pd.DateOffset(days=14) 
   df['date'] = df['date'].dt.date
   df = df.set_index('date')
   df = df.drop("Fecha y Hora", axis = 1)
   #
   r = pd.date_range(start="1/1/1807", end="12/1/2020", freq ="MS") + pd.DateOffset(days=14) 
   df = df.reindex(r)
   df = df["Caudal Medio Mensual [m3/seg]"]
   return df, A

#####################
# Initialize NETCDF
###############
# DATE
# Date - extension 1807 - 2018
# Brazilian and Argentinian station are only from 1900
# Fin the index to adjust

def savetonetcdf(dncout, dir_grdc, dmetafile):
    dfmeta = getdfmeta(dmetafile)
    
    date = np.array([datetime(1807+i//12,i%12+1,15) for i in range(0,214*12)])
    date_nc = [date2num(d,"seconds since 1807-01-15 00:00:00", calendar = "gregorian") for d in date]

    y = np.array([d.year for d in date])
    m = np.array([d.month for d in date])
    index_start = np.where(y == 1900)[0][0]

    FillValue = 1e+20

    with Dataset(orig+"Argentina_Discharge_AS2020.nc", "w") as foo, Dataset(dir_grdc, "r") as grdc:
        foo.history = "Created " + datetime.today().strftime('%Y-%m-%d')
        # Copy dimension from GRDC
        for dimn in grdc.dimensions:
          if dimn == "stations":
            numst = len(glob.glob(dire))
            foo.createDimension(dimn, numst) # remplire
          elif dimn == "time":
            foo.createDimension(dimn, len(date))
          else:
            foo.createDimension(dimn, grdc.dimensions[dimn].size)
      
        # Copy variables
        for varn in grdc.variables:
          if varn not in ["calculatedhydro", "mergedhydro", "flags","alt_hydrograph", "alternative_index"]:
            ovar = grdc.variables[varn]
          if varn in ["time", "hydrographs",  ]:
            newvar = foo.createVariable(varn, ovar.dtype, ovar.dimensions, zlib = True, fill_value=FillValue)
          else:      
            newvar = foo.createVariable(varn, ovar.dtype, ovar.dimensions,       zlib = True)
          for attrn in ovar.ncattrs():
            if attrn != "_FillValue":
              attrv = ovar.getncattr(attrn)
              newvar.setncattr(attrn,attrv)
      
        foo.variables["time"][:] = date_nc[:]
        foo.variables["country"][:] = stringtochar(np.array("AR", dtype ="S60"))[:]
  
        L = glob.glob(dire)
        DATA = [get_data(d, dfmeta) for d in L] 
        DStation = [get_info_st(A) for df,A in DATA] 
        WMO = np.array(
          [WMO.stations(
              D["lon"],
              D["lat"])
              for D in DStation])
        idWMO = np.unique(WMO)
        idWMO = {wm:9999 for wm in idWMO}
      
        for k, d in enumerate(L):
          df, A = DATA[k]
          D = DStation[k]
          #
          stReg = WMO[k]//100
          stSubreg = WMO[k]%100
          foo.variables["WMOreg"][k] = stReg
          foo.variables["WMOsubreg"][k] = stSubreg
          stcode = stReg*1e6 + stSubreg*1e4 +idWMO[WMO[k]]
          idWMO[WMO[k]]-=1
      
          # CHARACTER VARIABLES
          for varn in L_varstr:
            foo.variables[varn][k,:] = stringtochar(np.array(D[varn], dtype ="S60"))[:]
          # NUMERICAL VARIABLE
          for varn in L_varfloat:
            foo.variables[varn][k] = D[varn]
          # CODE
          foo.variables["number"][k] = stcode
      
          for varn in ["hydrographs"]:
            data = np.full(len(date_nc), FillValue)
            hydro = df.to_numpy()
            
            data[:] = df.to_numpy()[:]
            foo.variables[varn][:,k] = data [:]
      
        ## GLOBAL ATTRIBUTES
        globAttrs = {
          "history" : "Monthly discharge dataset - Argentina",
          "metadata" : "Missing metadata are replaced by XXX or -999",
          "Source" : "From BDHI, Argentina",
          "MergeSource1" : "Red Hidrologica Nacional, Argentina",
          "ConversionDate" : "2020-12-23",
          }
        for g in globAttrs.keys():
          foo.setncattr(g,globAttrs[g])
        foo.sync()    

