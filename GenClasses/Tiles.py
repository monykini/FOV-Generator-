from pyproj import Transformer
import mercantile
import math
import requests
from PIL import Image
import json
from io import BytesIO
import numpy as np
from .Shapes import Points
from shapely.geometry import Point, Polygon, LineString
import os
from FOV.settings import PROCESSED_TILES_DIRECTORY,PROCESSED_TILES_DIRECTORY_NAME
from generator.models import modelPoint,modelUserMarker
from django.contrib.gis.gdal import GDALRaster
from django.contrib.gis import geos
from numba import jit , njit



class tileGatherer():
    """
    get tiles according to user marker \n
    tileGatherer(userMarker) \n
    methods: \n
    conver_raster_tiles(self) := gets array of points from raster tiles\n
    get_tiles(self) := gets mercantile tiles numbers  \n

    """
    def __init__(self,userMarker):
        self.areaArray = []
        self.userMarker = userMarker
        self.converter = latlon_to_pixal_Converter()
    

    def get_tiles(self):
        tiles = []
        square_4326 = self.userMarker
        for p in square_4326:
                mercent = mercantile.tile(p[1],p[0],15)
                tiles.append([mercent.x,mercent.y])

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
        return total_tiles_matrix

    def check_files(self,total_tiles_matrix):
        remove = []
        print(total_tiles_matrix)
        for x in range(len(total_tiles_matrix)):
                for y in range(len(total_tiles_matrix[x])):
                        check = 0
                        for i in range(0,512,256):
                                for j in range(0,512,256):
                                        x_pixal_world = (i+(512*total_tiles_matrix[x][y][0]))
                                        y_pixal_world = (j+(512*total_tiles_matrix[x][y][1]))
                                        lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                        if modelPoint.objects.filter(wsg48Point = geos.Point(lon,lat) ).exists():
                                                check += 1
                        if check >= 3:
                                remove.append([x,y])
        print(remove)
        for r in remove[::-1]:
               del total_tiles_matrix[r[0]][r[1]]
        return total_tiles_matrix
        

    def get_raster_tiles(self,total_tiles_matrix):
        filled_tiles_matrix = []

        for t in total_tiles_matrix:
                temp=[]
                for y in t:
                        req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.jpg90?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                        req = requests.get(req)
                        image = Image.open(BytesIO(req.content))
                        data = np.asarray(image)
                        temp.append(data)
                filled_tiles_matrix.append(temp)

        return total_tiles_matrix,filled_tiles_matrix



    def conver_raster_tiles(self):
        if len(self.areaArray) > 0 :
            return self.areaArray
        total_tiles_matrix = self.check_files(self.get_tiles())
        total_tiles_matrix , filled_tiles_matrix  = self.get_raster_tiles(total_tiles_matrix)
        print(total_tiles_matrix)
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")

        for x in range(len(total_tiles_matrix)):
                for y in range(len(total_tiles_matrix[x])):
                        for i in range(512):
                                for j in range(512):
                                        x_pixal_world = (i+(512*total_tiles_matrix[x][y][0]))
                                        y_pixal_world = (j+(512*total_tiles_matrix[x][y][1]))
                                        x_pixal=i+(x*512)
                                        y_pixal=j+(y*512)
                                        lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                        color = list(filled_tiles_matrix[x][y][i][j])
                                        color = [float(color[0]),float(color[1]),float(color[2]),float(color[3])]
                                        maerc_lat,maerc_lon = transformer.transform(lat, lon)
                                        height = float(-10000 + ((color[0] * 256 * 256 + color[1] * 256 + color[2]) * 0.1))
                                        try:
                                                modelPoint.objects.create(wsg48Point = geos.Point(lon,lat) ,macPoint = geos.Point(maerc_lon,maerc_lat),color=json.dumps(color),pixal_xy=json.dumps([x_pixal,y_pixal]),world_pixal_xy=json.dumps([x_pixal_world,y_pixal_world]),height=height )
                                        except:
                                                pass
        print('ok')         
        return self.areaArray




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