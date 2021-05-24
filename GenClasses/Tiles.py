import django

django.setup()

from generator.models import modelPoint,modelUserMarker,buildingData
from django.contrib.gis.gdal import GDALRaster
from django.contrib.gis import geos

from .Shapes import Points
from FOV.settings import PROCESSED_TILES_DIRECTORY,PROCESSED_TILES_DIRECTORY_NAME


# from shapely.geometry import Point, Polygon, LineString


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
import threading
# import sys
# import numpy


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
                        print(location)
                        if location.get('city',None) != None:
                                if {'city':location['city'],'country':location['country']} not in locations: 
                                        locations.append({'city':location['city'],'country':location['country']})
                        if location.get('region',None) != None:
                                if {'city':location['region'].split(' ')[0],'country':location['country']} not in locations: 
                                        locations.append({'city':location['region'].split(" ")[0],'country':location['country']})
                print(locations)
                valid_raster = []
                lats_y = [s[0] for s in square]
                lons_x = [s[1] for s in square]
                max_x,max_y,min_x,min_y = max(lons_x)+0.001,max(lats_y)+0.001,min(lons_x)-0.001,min(lats_y)-0.001
                temp_square = []
                for s in square:
                        if s[0] == max_x:
                                s[0] = max_x + 0.01
                        if s[0] == min_x:
                                s[0] = min_x - 0.01
                        if s[1] == max_y:
                                s[1] = max_y + 0.01
                        if s[1] == min_y:
                                s[1] = min_y - 0.01
                        temp_square.append(s)

                userPolygon = [ s[::-1] for s in temp_square ]
                userPolygon = geometry.Polygon(userPolygon)
                
                for l in locations:
                        path = f"rasters/{l['country']}/{l['city']}"
                        files = glob.glob(path+"/*.tif")
                        for f in files:
                                
                                bounds = self.get_raster_bounds(filename = f)
                                rasterPolygon = geometry.Polygon(bounds)
                                
                                if userPolygon.intersects(rasterPolygon):
                                        valid_raster.append(f)
                                        # print(bounds)
                raster = None
                userRasterPath = f"userRasters/{self.markerObject.user.username}/"
                if len(valid_raster) > 1:
                        files_to_mosaic = valid_raster # However many you want.
                        g = gdal.Warp(userRasterPath+"combined.tif", files_to_mosaic, format="GTiff",
                                options=["COMPRESS=LZW", "TILED=YES"]) # if you want
                        g = None
                        raster = userRasterPath+"combined.tif"
                else:
                      raster = valid_raster[0]
                
                
                clipped_filename = f"cliped-{self.markerObject.id}.tif" 
                
                lats_y = [s[0] for s in square]
                lons_x = [s[1] for s in square]
                max_x,max_y,min_x,min_y = max(lons_x),max(lats_y),min(lons_x),min(lats_y) 
                
                ds=gdal.Open(raster)
                ds = gdal.Translate(userRasterPath+clipped_filename, ds,projWin = [min_x-0.001, max_y+0.001, max_x+0.001,  min_y-0.001])#,xRes=0.00001, yRes=0.00001, resampleAlg="bilinear", format='vrt'

                ds = None  
                
                print([min_x, max_y, max_x,  min_y])
                
                fileName = self.update_raster(userRasterPath+clipped_filename)


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

        def update_dem(self,DEM_Value,start,end,Cell_Size,Origin_X,Origin_Y,buildings):
                for col_x in range(len(DEM_Value))[start:end]:
                        for row_y in range(len(DEM_Value[col_x])):
                                x = (Cell_Size*col_x)+Origin_X 
                                y = -((row_y*Cell_Size)-Origin_Y)
                                point = geos.Point(x,y)
                                for b in buildings:
                                        if b.geom.contains(point):
                                                DEM_Value[col_x][row_y] += b.height
                                                break

        def update_raster_with_buildings(self,fileName):
                # Input DEM
                # filename = raw_input("Input DEM FILE : ")

                dem = gdal.Open(fileName,gdal.GA_ReadOnly)
                geotransform = dem.GetGeoTransform()
                DEM_Value = np.array(dem.GetRasterBand(1).ReadAsArray(), dtype ="float") #Raster to Array
                # numpy.set_printoptions(threshold=sys.maxsize)
                print(DEM_Value)
                # lol
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
                        print(Cell_Size,"cell")
                        print(geotransform[5],"cell")
                        CRS = dem.GetProjection() # make sure that CRS is on geographic coordinate system because you use lat/long 
                        points = []
                        size = len(DEM_Value)
                        division = math.ceil(size/10)
                        threads = []
                        for d in range(10):
                                threads.append(threading.Thread(target=self.update_dem, args=(DEM_Value,d*division,(d+1)*division,Cell_Size,Origin_X,Origin_Y,buildings),))
                                threads[d].start()
                        for d in range(10):
                                threads[d].join()
                        # for col_x in range(len(DEM_Value)):
                        #         for row_y in range(len(DEM_Value[col_x])):
                        #                 x = (Cell_Size*col_x)+Origin_X 
                        #                 y = -((row_y*Cell_Size)-Origin_Y)
                        #                 point = geos.Point(x,y)
                        #                 for b in buildings:
                        #                         if b.geom.contains(point):
                        #                                 DEM_Value[col_x][row_y] += b.height
                        #                                 break
                return DEM_Value

        def GetGeoInfo(self,FileName):
                SourceDS = gdal.Open(FileName, gdal.GA_ReadOnly)
                NDV = SourceDS.GetRasterBand(1).GetNoDataValue()
                xsize = SourceDS.RasterXSize
                ysize = SourceDS.RasterYSize

                print(xsize,ysize)
                GeoT = SourceDS.GetGeoTransform()
                Projection = osr.SpatialReference()
                Projection.ImportFromWkt(SourceDS.GetProjectionRef())
                DataType = SourceDS.GetRasterBand(1).DataType
                DataType = gdal.GetDataTypeName(DataType)
                return NDV, xsize, ysize, GeoT, Projection, DataType

        # Function to write a new file.
        def CreateGeoTiff(self,Name, Array, driver, NDV,xsize, ysize, GeoT, Projection, DataType):
                if DataType == 'Float32':
                        DataType = gdal.GDT_Float32
                if DataType == "Int16":
                        DataType = gdal.GDT_Int16
                NewFileName = Name+'.tif'
                # Set nans to the original No Data Value
                Array[np.isnan(Array)] = NDV
                # Set up the dataset
                DataSet = driver.Create( NewFileName, xsize, ysize, 1, DataType )
                        # the '1' is for band 1.
                DataSet.SetGeoTransform(GeoT)
                DataSet.SetProjection( Projection.ExportToWkt() )
                # Write the array
                DataSet.GetRasterBand(1).WriteArray( Array )
                DataSet.GetRasterBand(1).SetNoDataValue(NDV)

                return NewFileName


        def update_raster(self,FileName):        
                # Open the original file
                                                
                DataSet = gdal.Open(FileName, gdal.GA_ReadOnly)
                # Get the first (and only) band.
                Band = DataSet.GetRasterBand(1)
                # Open as an array.
                # Array = Band.ReadAsArray()
                # Get the No Data Value
                NDV = Band.GetNoDataValue()
                # Convert No Data Points to nans
                # Array[Array == NDV] = np.nan

                # Now I do some processing on Array, it's pretty complex 
                # but for this example I'll just add 20 to each pixel.
                NewArray = self.update_raster_with_buildings(FileName)  # If only it were that easy

                # Now I'm ready to save the new file, in the meantime I have 
                # closed the original, so I reopen it to get the projection
                # information...
                NDV, xsize, ysize, GeoT, Projection, DataType = self.GetGeoInfo(FileName)

                # Set up the GTiff driver
                driver = gdal.GetDriverByName('GTiff')

                # Now turn the array into a GTiff.
                clipped_filename = f"cliped-{self.markerObject.id}.tif" 
                FileName = FileName.replace(clipped_filename,'')
                NewFileName = self.CreateGeoTiff(FileName+ f'cliped-{self.markerObject.id}_updated', NewArray, driver, NDV, 
                                        xsize, ysize, GeoT, Projection, DataType)

                return NewFileName


        def get_tiles(self):
                tiles = []
                square_4326 = self.userMarker
                for p in square_4326:
                        mercent = mercantile.tile(p[1],p[0],15)
                        tiles.append([mercent.x,mercent.y])
                
                self.store_raster_clip(square_4326)

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
                                # decoded_data = -10000 + ((r * 256 * 256 + g * 256 + b) * 0.1)
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
