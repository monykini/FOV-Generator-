import django
from generator.models import modelPoint,modelUserMarker,buildingData
from django.contrib.gis.gdal import GDALRaster
from django.contrib.gis import geos

from .Shapes import Points
from FOV.settings import PROCESSED_TILES_DIRECTORY,PROCESSED_TILES_DIRECTORY_NAME


# from shapely.geometry import Point, Polygon, LineString

django.setup()

from pyproj import Transformer
import mercantile
import math
import requests
from PIL import Image
import json
from io import BytesIO
import os
from shapely import geometry
from numba import jit , njit
from multiprocessing import Pool
import time
import tifffile
import copy
from osgeo import gdal,ogr,osr
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import glob
import numpy as np

geolocator = Nominatim(user_agent="route")
geopygeocode = RateLimiter(geolocator.reverse, min_delay_seconds=1,max_retries=5)


class tileGatherer():
        """
        get tiles according to user marker \n
        tileGatherer(userMarker) \n
        methods: \n
        conver_raster_tiles(self) := gets array of points from raster tiles\n
        get_tiles(self) := gets mercantile tiles numbers  \n
        """
        def __init__(self,userMarker,*args,**kwargs):
                self.userMarker = userMarker
                self.converter = latlon_to_pixal_Converter()
                self.og_tiles = []
                self.markerID = kwargs.get("markerID",None)
                self.markerObject = kwargs.get("markerObject",None)
        

        def store_raster_clip(self,square):
                locations=[]
                for p in square:
                        location = (geopygeocode((p[0],p[1]),language='en').raw)['address']
                        if {'city':location['city'],'country':location['country']} not in locations: 
                                locations.append({'city':location['city'],'country':location['country']})
                
                valid_raster = []
                
                userPolygon = [ s[::-1] for s in square ]
                userPolygon = geometry.Polygon(userPolygon)
                
                for l in locations:
                        path = f"rasters/{l['country']}/{l['city']}"
                        files = glob.glob(path+"/*.tif")
                        print(files,'lol')
                        for f in files:
                                
                                bounds = self.get_raster_bounds(filename = f)
                                rasterPolygon = geometry.Polygon(bounds)
                                
                                if userPolygon.intersects(rasterPolygon):
                                        valid_raster.append(f)
                                        print(f)
                                        # print(bounds)
                raster = None
                if len(valid_raster) > 1:
                        pass
                else:
                      raster = valid_raster[0]
                
                userRasterPath = f"userRasters/{self.markerObject.user.username}/"
                clipped_filename = f"cliped-{self.markerObject.id}.tif" 
                
                lats_y = [s[0] for s in square]
                lons_x = [s[1] for s in square]
                max_x,max_y,min_x,min_y = max(lons_x),max(lats_y),min(lons_x),min(lats_y) 
                
                ds=gdal.Open(raster)
                ds = gdal.Translate(userRasterPath+clipped_filename, ds, projWin = [min_x-0.001, max_y+0.001, max_x+0.001,  min_y-0.001])
                ds = None  
                
                print([min_x, max_y, max_x,  min_y])
                
                self.update_raster_with_buildings(userRasterPath+clipped_filename)

                lol

        def GetExtent(self,ds):
                """ Return list of corner coordinates from a gdal Dataset """
                xmin, xpixel, _, ymax, _, ypixel = ds.GetGeoTransform()
                width, height = ds.RasterXSize, ds.RasterYSize
                xmax = xmin + width * xpixel
                ymin = ymax + height * ypixel

                return (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)

        def ReprojectCoords(self,coords,src_srs,tgt_srs):

                trans_coords=[]
                transform = osr.CoordinateTransformation( src_srs, tgt_srs)
                for x,y in coords:
                        x,y,z = transform.TransformPoint(x,y)
                        trans_coords.append([x,y])
                return trans_coords


        def get_raster_bounds(self,filename = None):
                if filename == None:
                        raster=r'data.tif'
                else:
                        raster = filename
                # print(raster)
                ds=gdal.Open(raster)
                # print(ds)
                ext=self.GetExtent(ds)
                # print(ext)
                # print(ds.RasterCount)
                src_srs=osr.SpatialReference()
                src_srs.ImportFromWkt(ds.GetProjection())
                #tgt_srs=osr.SpatialReference()
                #tgt_srs.ImportFromEPSG(4326)
                # print(src_srs)
                tgt_srs = src_srs.CloneGeogCS()
                # print(tgt_srs)
                geo_ext=self.ReprojectCoords(ext, src_srs, tgt_srs)
                return geo_ext

        def update_raster_with_buildings(self,fileName):
                # Input DEM
                # filename = raw_input("Input DEM FILE : ")
                print(fileName)
                dem = gdal.Open(fileName)
                geotransform = dem.GetGeoTransform()
                DEM_Value = np.array(dem.GetRasterBand(1).ReadAsArray(), dtype ="float") #Raster to Array
                bounds = self.get_raster_bounds(filename = fileName)
                bounds.append(bounds[0])
                bounds = tuple([tuple(b) for b in bounds])
                polygon = geos.Polygon(bounds)
                buildings = buildingData.objects.filter(geom__intersects = polygon)
                
                if len(buildings) > 0:
                        # Determine Basic Raster's Parameter
                        Col = dem.RasterXSize
                        Row = dem.RasterYSize
                        Origin_X = geotransform[0]
                        Origin_Y = geotransform[3]
                        Cell_Size = geotransform[1]
                        CRS = dem.GetProjection() # make sure that CRS is on geographic coordinate system because you use lat/long 
                        points = []
                        for col_x in range(len(DEM_Value)):
                                for row_y in range(len(DEM_Value[col_x])):
                                        x = (Cell_Size*col_x)+Origin_X 
                                        y = -((row_y*Cell_Size)-Origin_Y)
                                        point = geos.Point(x,y)
                                        for b in buildings:
                                                if point.intersects(b):
                                                        DEM_Value[col_x][row_y] += b.height
                                                        break
                        dem.GetRasterBand(1).WriteArray(DEM_Value)
                dem = None

        def get_tiles(self):
                tiles = []
                square_4326 = self.userMarker
                for p in square_4326:
                        mercent = mercantile.tile(p[1],p[0],15)
                        tiles.append([mercent.x,mercent.y])
                
                self.store_raster_clip(square_4326)
                lol

                x_matrix =  [ p[1] for p in tiles ]
                y_matrix = [p[0] for p in tiles]
                
                x_matrix_max , x_matrix_min = max(x_matrix) , min(x_matrix)
                y_matrix_max , y_matrix_min = max(y_matrix) , min(y_matrix) 

                total_x_axis_tiles = x_matrix_max-x_matrix_min+1
                total_y_axis_tiles = y_matrix_max-y_matrix_min+1

                top_left_tile = tiles[0]
                total_tiles_matrix=[]
                for x in range(total_x_axis_tiles):
                        temp=[]
                        for y in range(total_y_axis_tiles):
                                temp.append([top_left_tile[0]-y,top_left_tile[1]+x])
                        total_tiles_matrix.append(temp)

                total_tiles_matrix = total_tiles_matrix[::-1]
                self.og_tiles = copy.deepcopy(total_tiles_matrix)
                print(self.og_tiles,'tiles')
                # self.raster_to_tiff()
                return total_tiles_matrix

        def check_files(self,total_tiles_matrix):

                remove = []
                print(total_tiles_matrix)
                for x in range(len(total_tiles_matrix)):
                        for y in range(len(total_tiles_matrix[x])):
                                check = 0
                                for i in range(0,512,32):
                                        for j in range(0,512,511):
                                                x_pixal_world = (i+(512*total_tiles_matrix[x][y][0]))
                                                y_pixal_world = (j+(512*total_tiles_matrix[x][y][1]))
                                                lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                                if modelPoint.objects.filter(wsg48Point = geos.Point(lon,lat) ).exists():
                                                        check += 1
                                for j in range(0,512,511):
                                        x_pixal_world = (511+(512*total_tiles_matrix[x][y][0]))
                                        y_pixal_world = (j+(512*total_tiles_matrix[x][y][1]))
                                        lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                        if modelPoint.objects.filter(wsg48Point = geos.Point(lon,lat) ).exists():
                                                check += 1
                                if check >= 34:
                                        remove.append([x,y])
                print(remove)
                for r in remove[::-1]:
                        del total_tiles_matrix[r[0]][r[1]]
                return total_tiles_matrix
        
        def raster_to_tiff(self):  
                total_tiles_matrix = self.og_tiles
                print(self.og_tiles)
                transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
                for t in total_tiles_matrix:
                        temp=[]
                        for y in t:
                                req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.jpg90?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                                req = requests.get(req)
                                image = Image.open(BytesIO(req.content))
                                data = np.asarray(image)
                                image = tifffile.imwrite(f'{y[0]}-{y[1]}.tif', data, photometric='rgb')
                                src_filename =f'{y[0]}-{y[1]}.tif'
                                dst_filename = 'destination_ref.tif'
                                x_pixal_world = ((512*y[0]))
                                y_pixal_world = ((512*y[1]))
                                lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                maerc_lat,maerc_lon = transformer.transform(lat, lon)
                                # Opens source dataset
                                src_ds = gdal.Open(src_filename)
                                format = "GTiff"
                                driver = gdal.GetDriverByName(format)

                                # Open destination dataset
                                dst_ds = driver.CreateCopy(dst_filename, src_ds, 0)

                                # Specify raster location through geotransform array
                                # (uperleftx, scalex, skewx, uperlefty, skewy, scaley)
                                # Scale = size of one pixel in units of raster projection
                                # this example below assumes 100x100
                                gt = [maerc_lat, 2.245  , 0, maerc_lon , 0, -2.245 ]

                                # Set location
                                dst_ds.SetGeoTransform(gt)
                        
                                # Get raster projection
                                epsg = 3857
                                srs = osr.SpatialReference()
                                srs.ImportFromEPSG(epsg)
                                dest_wkt = srs.ExportToWkt()
                                print(dest_wkt,'lol')
                                # Set projection
                                dst_ds.SetProjection("""PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]""")

                                print(dst_ds.GetProjection())

                                # Close files
                                dst_ds = None
                                src_ds = None
                                lol


        def get_raster_tiles(self,total_tiles_matrix):
                filled_tiles_matrix = []
                print(total_tiles_matrix)
                for t in total_tiles_matrix:
                        temp=[]
                        for y in t:
                                req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.jpg90?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                                req = requests.get(req)
                                image = Image.open(BytesIO(req.content))
                                data = np.asarray(image)
                                # r = data[..., 0]
                                # g = data[..., 1]
                                # b = data[..., 2]
                                # decoded_data = (256*r + g + b/256) - 32768
                                # print(decoded_data)
                                # print('decoded_data')
                                temp.append(data)
                        filled_tiles_matrix.append(temp)
                
                return total_tiles_matrix,filled_tiles_matrix



        def convert_raster_tiles(self):
                t1 = time.perf_counter()

                total_tiles_matrix = self.check_files(self.get_tiles())
                total_tiles_matrix , filled_tiles_matrix  = self.get_raster_tiles(total_tiles_matrix)

                pool = Pool(processes=16)

                for x in range(len(total_tiles_matrix)):
                        for y in range(len(total_tiles_matrix[x])):
                                pools=[]
                                for k in range(16):
                                        pools.append(pool.apply_async(self.decode_tile, args=(total_tiles_matrix[x][y],32*k,(32*(k+1)),filled_tiles_matrix[x][y])))
                                for k in range(16):
                                        pools[k].wait()
                                        
                t2 = time.perf_counter()
                print(f"{t2-t1} Seconds")
                # self.raster_to_tiff()

        def decode_tile(self,tile,iStartRange,iEndRange,filledTile):
                transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
                for i in range(512)[iStartRange:iEndRange]:
                        for j in range(512):
                                x_pixal_world = (i+(512*tile[0]))
                                y_pixal_world = (j+(512*tile[1]))

                                x_pixal,y_pixal=i,j

                                lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)

                                color = list(filledTile[i][j])
                                color = [float(color[0]),float(color[1]),float(color[2]),float(color[3])]

                                maerc_lat,maerc_lon = transformer.transform(lat, lon)

                                height = float(-10000 + ((color[0] * 256 * 256 + color[1] * 256 + color[2]) * 0.1))
                                if height != 0 :
                                        try:
                                                modelPoint.objects.create(wsg48Point = geos.Point(lon,lat) ,macPoint = geos.Point(maerc_lon,maerc_lat),color=json.dumps(color),pixal_xy=json.dumps([x_pixal,y_pixal]),world_pixal_xy=json.dumps([x_pixal_world,y_pixal_world]),height=height )
                                        except:
                                                pass



class latlon_to_pixal_Converter():

        def ClipByRange(self,n, range):
                return n % range

        def Clip(self,n, minValue, maxValue):
                return min(max(n, minValue), maxValue)

        def PixelXYToLatLongOSM(self,pixelX,pixelY,zoomLevel):

                mapSize = math.pow(2, zoomLevel) * 512
                tileX = math.trunc(pixelX / 512)
                tileY = math.trunc(pixelY / 512)

                n = math.pi - ((2.0 * math.pi * (self.ClipByRange(pixelY, mapSize - 1) / 512)) / math.pow(2.0, zoomLevel))

                longitude = ((self.ClipByRange(pixelX, mapSize - 1) / 512) / math.pow(2.0, zoomLevel) * 360.0) - 180.0
                latitude = (180.0 / math.pi * math.atan(math.sinh(n)))
                return latitude,longitude
                
        def LatLongToPixelXYOSM(self,latitude ,longitude, zoomLevel):
                MinLatitude = -85.05112878
                MaxLatitude = 85.05112878
                MinLongitude = -180
                MaxLongitude = 180
                mapSize = math.pow(2, zoomLevel) * 512

                latitude = self.Clip(latitude, MinLatitude, MaxLatitude)
                longitude = self.Clip(longitude, MinLongitude, MaxLongitude)

                X = (longitude + 180.0) / 360.0 * (1 << zoomLevel)
                Y = (1.0 - math.log(math.tan(latitude * math.pi / 180.0) + 1.0 / math.cos(math.radians(latitude))) / math.pi) / 2.0 * (1 << zoomLevel)

                tilex = int(math.trunc(X))
                tiley = int(math.trunc(Y))

                pixelX = self.ClipByRange((tilex * 512) + ((X - tilex) * 512), mapSize - 1)
                pixelY = self.ClipByRange((tiley * 512) + ((Y - tiley) * 512), mapSize - 1)

                return int(pixelX) , int(pixelY)
