import json
import os, gdal
import mercantile
from generator.models import maxElevation,modelPoint
from django.contrib.gis.gdal import GDALRaster
import numpy as np
from shapely.geometry import Point
from numba import jit , njit
from numba import int64, float64
from numba.experimental import jitclass
import math
import time

world_shp = f'buidlingsData/elevation/'
input_name ='30n060e_20101117_gmted_max075.tif'
rasterout = 'buidlingsData/elevation/'
output_filename = 'tile_'

tile_size_x = 512
tile_size_y = 512



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


def decode_tile(self,tile,iStartRange,iEndRange,filledTile):
    print([iStartRange,iEndRange])
    for i in range(512)[iStartRange:iEndRange]:
            for j in range(512):
                    print(i,j)
                    print([iStartRange,iEndRange])
                    transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
                    x_pixal_world = (i+(512*tile[0]))
                    y_pixal_world = (j+(512*tile[1]))
                    x_pixal=i
                    y_pixal=j
                    lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                    color = list(filledTile[i][j])
                    color = [float(color[0]),float(color[1]),float(color[2]),float(color[3])]
                    maerc_lat,maerc_lon = transformer.transform(lat, lon)
                    height = float(-10000 + ((color[0] * 256 * 256 + color[1] * 256 + color[2]) * 0.1))
                    try:
                            modelPoint.objects.create(wsg48Point = geos.Point(lon,lat) ,macPoint = geos.Point(maerc_lon,maerc_lat),color=json.dumps(color),pixal_xy=json.dumps([x_pixal,y_pixal]),world_pixal_xy=json.dumps([x_pixal_world,y_pixal_world]),height=height )
                    except:
                            pass


def run(verbose=True):







