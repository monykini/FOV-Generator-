import django

django.setup()

from generator.models import modelPoint,modelUserMarker,buildingData,MLbuildingData,MLtreesData
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
import pandas as pd
from GenClasses import buildingML 
import random
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
        
        def get_tiles(self):
                tiles = []
                square_4326 = self.userMarker
                for p in square_4326:
                        print(p[1],p[0])
                        mercent = mercantile.tile(p[1],p[0],15)
                        tiles.append([mercent.x,mercent.y])
                

                x_matrix =  [ p[1] for p in tiles ]
                y_matrix = [p[0] for p in tiles]
                
                x_matrix_max , x_matrix_min = max(x_matrix) , min(x_matrix)
                y_matrix_max , y_matrix_min = max(y_matrix) , min(y_matrix)
                print(x_matrix_max , x_matrix_min)
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
                self.get_buildings_ML(square_4326)
                return total_tiles_matrix
        

        def get_buildings_ML(self,square_4326):
                marker = modelUserMarker.objects.get(id=  self.markerID)
                polygons, treepolygons = buildingML.get_tiles_ML(square_4326,self.converter.PixelXYToLatLongOSM,marker)
                for p in polygons:
                        MLbuildingData.objects.create(marker=marker,height = random.randint(3,5) , geom = p)
                
                for p in treepolygons:
                        MLtreesData.objects.create(marker=marker,height = random.randint(3,4) , geom = p)



        def check_files(self,total_tiles_matrix):

                remove = []
                print(total_tiles_matrix)
                for x in range(len(total_tiles_matrix)):
                        for y in range(len(total_tiles_matrix[x])):
                                check = 0
                                for i in range(0,512,32):
                                        for j in range(0,512,511):
                                                x_pixal_world = (j+(512*total_tiles_matrix[x][y][0]))
                                                y_pixal_world = (i+(512*total_tiles_matrix[x][y][1]))
                                                lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                                if modelPoint.objects.filter(wsg48Point = geos.Point(lon,lat) ).exists():
                                                        check += 1
                                for j in range(0,512,511):
                                        x_pixal_world = (511+(512*total_tiles_matrix[x][y][0]))
                                        y_pixal_world = (i+(512*total_tiles_matrix[x][y][1]))
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
                                req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.png256?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                                print(req)
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
                print('ok')
                total_tiles_matrix = self.check_files(self.get_tiles())
                total_tiles_matrix , filled_tiles_matrix  = self.get_raster_tiles(total_tiles_matrix)

                # pool = Pool(processes=10)

                for x in range(len(total_tiles_matrix)):
                        for y in range(len(total_tiles_matrix[x])):
                                pools=[]
                                for k in range(16):
                                        pools.append(threading.Thread(target = self.decode_tile, args=(total_tiles_matrix[x][y],32*k,(32*(k+1)),filled_tiles_matrix[x][y])))
                                        pools[k].start()
                                for k in range(16):
                                        pools[k].join()
                                        
                t2 = time.perf_counter()
                print(f"{t2-t1} Seconds")
                square_4326 = self.userMarker

        def decode_tile(self,tile,iStartRange,iEndRange,filledTile):
                transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
                for i in range(0,512)[iStartRange:iEndRange]:
                        for j in range(0,512):
                                y_pixal_world = (i+(512*tile[1]))
                                x_pixal_world = (j+(512*tile[0]))

                                x_pixal,y_pixal=j,i

                                lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)

                                color = list(filledTile[i][j])
                                color = [float(color[0]),float(color[1]),float(color[2]),float(color[3])]

                                maerc_lat,maerc_lon = transformer.transform(lat, lon)

                                height = float(-10000 + (((color[0] * 256 * 256) + (color[1] * 256) + color[2]) * 0.1))
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
