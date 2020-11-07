import pandas as pd
import numpy as np
import datetime
from shapely.geometry import Point, Polygon, LineString
import pyproj
from pyproj import Proj, transform
import numpy as np
# from scipy.spatial import ConvexHull
# import geopandas as gpd
import six
import shapely
from pyproj import Transformer
import mercantile
from PIL import Image
import math
import requests
import json
from io import BytesIO

def ClipByRange(n, range):
        return n % range

def Clip(n, minValue, maxValue):
    return min(max(n, minValue), maxValue)

def PixelXYToLatLongOSM(pixelX,pixelY,zoomLevel):

        mapSize = math.pow(2, zoomLevel) * 256
        tileX = math.trunc(pixelX / 256)
        tileY = math.trunc(pixelY / 256)

        n = math.pi - ((2.0 * math.pi * (ClipByRange(pixelY, mapSize - 1) / 256)) / math.pow(2.0, zoomLevel))

        longitude = ((ClipByRange(pixelX, mapSize - 1) / 256) / math.pow(2.0, zoomLevel) * 360.0) - 180.0
        latitude = (180.0 / math.pi * math.atan(math.sinh(n)))
        # print(latitude,longitude)
        return latitude,longitude




transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
lat = 33.64013671875;
lon = 73.0455032;
x1,y1 = 33.6466897,73.0455032
# lon first lat last fuck
mercent = mercantile.tile(lon,lat ,15)
x2,y2 = transformer.transform(lat, lon)
point = shapely.geometry.Point(x2,y2)
#anti-clock wise top - right corner
og_square = point.buffer(500, cap_style=3)
square = list(og_square.exterior.coords)
print(square)
transformer = Transformer.from_crs("epsg:3857","epsg:4326")
square_4326 = []
for p in range(len(square)-1):
        x,y = transformer.transform(square[p][0], square[p][1])
        square_4326.append([x,y])
print(square_4326)

tiles = []
for p in square_4326:
        mercent = mercantile.tile(p[1],p[0],15)
        print(mercent)
        tiles.append([mercent.x,mercent.y])

#-----y-axis is first------------------------
print(tiles,"tiles")
total_x_axis_tiles = tiles[1][1]-tiles[0][1]+1
total_y_axis_tiles = tiles[1][0]-tiles[2][0]+1
print(total_x_axis_tiles,total_y_axis_tiles)
#------here the corner are reset to proper form------
top_left_tile = tiles[0]
total_tiles_matrix=[]
for x in range(total_x_axis_tiles):
        temp=[]
        for y in range(total_y_axis_tiles):
                temp.append([top_left_tile[0]-x,top_left_tile[1]+y])
        total_tiles_matrix.append(temp)

total_tiles_matrix = total_tiles_matrix[::-1]
print(np.array(total_tiles_matrix))
# tiles_mesh = np.zeros()
filled_tiles_matrix = []
f = open("myfile1.txt", "w")

for t in total_tiles_matrix:
        temp=[]
        for y in t:
                req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.pngraw?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                req = requests.get(req)
                image = Image.open(BytesIO(req.content))
                data = np.asarray(image)
                temp.append(data)
        filled_tiles_matrix.append(temp)


transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
cords_tiles_matrix = []
for x in range(len(total_tiles_matrix)):
        temp = []
        for y in range(len(total_tiles_matrix[x])):
                pixals_per_tile= []
                for i in range(256):
                        temp2=[]
                        for j in range(256):
                                x_pixal_world = (i+(256*total_tiles_matrix[x][y][0]))-256
                                y_pixal_world = (j+(256*total_tiles_matrix[x][y][1]))-256
                                x_pixal=(x+1)*i
                                y_pixal=(y+1)*j
                                lat,lon = PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                color = filled_tiles_matrix[x][y][i][j]
                                maerc_lat,maerc_lon = transformer.transform(lat, lon)
                                height = -10000 + ((color[1] * 256 * 256 + color[2] * 256 + color[3]) * 0.1)
                                data={"world_xy_pixal":[x_pixal_world,y_pixal_world],'lat/lon(inorder)':[lat,lon],"pixal_x_y":[x_pixal,y_pixal],'color':color , 'Mercator':[maerc_lat,maerc_lon] , 'elevation(meter)':height}
                                temp2.append([lat,lon])
                                f.write(f'{lat},{lon},{color},{[x_pixal_world,y_pixal_world]},{[x_pixal,y_pixal]},{[height]}\n')
                        pixals_per_tile.append(temp2)
                temp.append(pixals_per_tile)
        cords_tiles_matrix.append(pixals_per_tile)



















# for t in total_tiles_matrix:
#         temp=[]
#         for y in t:
#                 req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.pngraw?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
#                 req = requests.get(req)
#                 image = Image.open(BytesIO(req.content))
#                 data = np.asarray(image)
#                 temp.append(data)
#         filled_tiles_matrix.append(temp)

# print(filled_tiles_matrix)







# https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/15/23033/13128@2x?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ for static street view
# print (x2,y2)
# # temp = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{tiles[0][0]}/{tiles[0][1]}@2x.pngraw?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
# print(temp)
# req = requests.get(temp)
# print(req.status_code)
# # image = Image.open('3228@2x.png')
# image = Image.open(BytesIO(req.content))
# data = np.asarray(image)
# # data = data.flatten()
# print(data)
