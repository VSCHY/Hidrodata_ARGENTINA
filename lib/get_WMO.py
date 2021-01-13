import cartopy.io.shapereader as shpreader
from shapely.geometry import Polygon, Point, MultiPolygon
import numpy as np
import shapefile


class WMOREG:
    """
    Quick use : 
    WMO = WMOREG(dfile)
    WMOreg, WMOsubreg = WMO.stations(lon,lat)
    """
    def __init__(self, dfile):
        """
        dfile : direction of the file : wmobb_basins.shp
        Download at ftp://ftp.bafg.de/pub/REFERATE/GRDC/wmo_basins_shp.zip
        """
        self.polygonWMO = []
        self.attributesPolygonWMO = []
        self.dfile = dfile
        geo_reg= shpreader.Reader(dfile)
        geo_reg = shapefile.Reader(dfile)
        feature = geo_reg.records
        for k,sr in enumerate(geo_reg.iterShapeRecords()):
          rec = sr.record
          geom = sr.shape.points
          try: 
            poly = Polygon(geom)
          except:
            poly = MultiPolygon(geom) # Polygon
          self.polygonWMO.append(poly)
          self.attributesPolygonWMO.append([rec["REGNUM"], rec["WMO306_MoC"]])

    def stations(self, lon, lat, output = "num"):
        """
        Get the WMOreg and WMOsubreg indexes
        lon, lat: longitude and latitude of the point.
        output: format of the output -> "num" (default) or "list"
        
        eg. WMOreg = 3 and WMOsubreg = 19
        -> num: 319; list: [3,19]  
        """
        # Point is (x,y)-(lon,lat) 
        p1 = Point(lon, lat)
        out = np.array([p1.within(poly) for poly in self.polygonWMO])
        try : 
            index = np.where(out)[0][0]
            stReg, stSubreg = self.attributesPolygonWMO[index]
            if output=="num":
                return stReg*100+stSubreg
            elif output == "list":
                return [stReg, stSubreg]
        except:
            print("lon: {0}; lat: {1}".format(lon,lat))
            print("No valid WMO region has been found, verify the lon lat")

