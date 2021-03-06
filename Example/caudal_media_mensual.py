import sys
sys.path.append("../lib")
from download import SNIH
from export_netcdf import savetonetcdf
import os

###################### 
           
# Direction to download the files
dir_out = "/home/anthony/Documents/LOCAL/DISCHARGE_DATABASE_V1/BDHI/Hidrodata_ARGENTINA/Example/OUTPUT/"


######################

"""
DOWNLOAD THE FILES
"""
"""
if not os.path.exists(dir_out):
    os.mkdir(dir_out)
else:
    print("The output repertory already exists, please remove all the pre-existing files")

website = SNIH(dir_out)

# Subselection of stations with "Tipo" = "HA", "M", "HM", "HMA":
website.getListaEstaciones(var = "Tipo", 
                           varValues = ["HA", "M", "HM", "HMA"])

# Save only the metadata:
#     for all the station (in nameFull)
#     for the station selected (in nameSubselection)
website.metaStationsDataframe(
              nameFull = dir_out + "BDHI_Estaciones_RedHidNac_full.csv", 
              nameSubselection = dir_out + "BDHI_Estaciones_RedHidNac_selectionCaudal.csv")

# Download the files
for index in website.subselection.keys():
   website.download_st(index)
"""
######################

"""
EXPORT IN NETCDF
"""

# Directory with the output
dischargeFilePath = "./OUTPUT/*xlsx"

# GRDC file adjust depending on the repertory
orig = "../../../Originals/"
dir_grdc = orig + "GRDC_Monthly_Jan20_v1.1.nc"


if not os.path.exists(dir_grdc):
    print("GRDC file does not exists please change the directory")
    sys.exit()
# Output
dncout = orig + "Argentina_Discharge_AS2020.nc"
# Meta file
dmetafile = "./OUTPUT/BDHI_Estaciones_RedHidNac_full.csv"

savetonetcdf(dncout, dir_grdc, dmetafile, dischargeFilePath)
