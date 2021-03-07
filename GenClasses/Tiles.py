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
        square_4326 = list(self.userMarker.get_square_4326().exterior.coords)
        for p in square_4326:
                mercent = mercantile.tile(p[1],p[0],15)
                print(mercent)
                tiles.append([mercent.x,mercent.y])

        x_matrix =  [ p[1] for p in tiles ]
        y_matrix = [p[0] for p in tiles]
        
        x_matrix_max , x_matrix_min = max(x_matrix) , min(x_matrix)
        y_matrix_max , y_matrix_min = max(y_matrix) , min(y_matrix) 

        total_x_axis_tiles = x_matrix_max-x_matrix_min+1
        total_y_axis_tiles = y_matrix_max-y_matrix_min+1

        print(total_x_axis_tiles , total_y_axis_tiles)
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
        print(total_tiles_matrix)
        remove = []
        for x in range(len(total_tiles_matrix)):
                for y in range(len(total_tiles_matrix[x])):
                        for file in os.listdir(PROCESSED_TILES_DIRECTORY):
                                if file.endswith(f"{total_tiles_matrix[x][y][0]},{total_tiles_matrix[x][y][1]}.json"):
                                        temp_file = open(f'{PROCESSED_TILES_DIRECTORY_NAME}/{total_tiles_matrix[x][y][0]},{total_tiles_matrix[x][y][1]}.json', "r").readlines()
                                        for line in temp_file:
                                                data = json.loads(line)
                                                if Point(data["Mercator"][0],data["Mercator"][1]).intersects(self.userMarker.square):
                                                        point = Points([data["lat"],data["lon"]], data["Mercator"], [data["pixal_X"],data["pixal_Y"]] , [data["world_pixal_X"],data["world_pixal_Y"]] , data["height"] , data["color"])
                                                        self.areaArray.append(point)

                                        remove.append([x,y])
                                        # print(os.path.join("/mydir", file))
        print(remove)
        for r in remove:
                del total_tiles_matrix[r[0]][r[1]]
        print(total_tiles_matrix)
        return total_tiles_matrix
        
    def get_raster_tiles(self):
        total_tiles_matrix = self.get_tiles()
        filled_tiles_matrix = []

        for t in total_tiles_matrix:
                temp=[]
                for y in t:
                        req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.jpg90?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                        print(req)
                        req = requests.get(req)
                        image = Image.open(BytesIO(req.content))
                        data = np.asarray(image)
                        temp.append(data)
                filled_tiles_matrix.append(temp)

        return total_tiles_matrix,filled_tiles_matrix



    def conver_raster_tiles(self):
        if len(self.areaArray) > 0 :
            return self.areaArray
        total_tiles_matrix , filled_tiles_matrix  = self.get_raster_tiles()
        print('conver_raster_tiles')
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        cords_tiles_matrix = []
        flat_array_cords_tiles_matrix=self.areaArray
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
                                        # data = Points([lat,lon], [maerc_lat,maerc_lon] , [x_pixal,y_pixal] , [x_pixal_world,y_pixal_world] , height , color)
                                        if not modelPoint.objects.filter(wsg48Point=geos.Point(lon,lat)).exists():
                                                p = modelPoint(wsg48Point = geos.Point(lon,lat) ,macPoint = geos.Point(maerc_lon,maerc_lat),color=json.dumps(color),pixal_xy=json.dumps([x_pixal,y_pixal]),world_pixal_xy=json.dumps([x_pixal_world,y_pixal_world]),height=height )
                                                p.save()
                                        else:
                                                break
                                        # flat_array_cords_tiles_matrix.append(data)
                                else:
                                        continue
                                
                                break

        print('conver_raster_tilesdone')
        # self.areaArray = flat_array_cords_tiles_matrix
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
                # print(latitude,longitude)
                return latitude,longitude
                
        def LatLongToPixelXYOSM(self,latitude ,longitude, zoomLevel):
                MinLatitude = -85.05112878
                MaxLatitude = 85.05112878
                MinLongitude = -180
                MaxLongitude = 180
                mapSize = math.pow(2, zoomLevel) * 256

                latitude = self.Clip(latitude, MinLatitude, MaxLatitude)
                longitude = self.Clip(longitude, MinLongitude, MaxLongitude)

                X = (longitude + 180.0) / 360.0 * (1 << zoomLevel)
                Y = (1.0 - math.log(math.tan(latitude * math.pi / 180.0) + 1.0 / math.cos(math.radians(latitude))) / math.pi) / 2.0 * (1 << zoomLevel)

                tilex = int(math.trunc(X))
                tiley = int(math.trunc(Y))

                pixelX = self.ClipByRange((tilex * 256) + ((X - tilex) * 256), mapSize - 1)
                pixelY = self.ClipByRange((tiley * 256) + ((Y - tiley) * 256), mapSize - 1)

                return pixelX , pixelY