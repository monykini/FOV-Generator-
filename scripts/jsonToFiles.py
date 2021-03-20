import json
import os, gdal
import mercantile
from generator.models import maxElevation
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





def run(verbose=True):
    ds = gdal.Open(world_shp + input_name)
    band = ds.GetRasterBand(1)
    xsize = band.XSize
    ysize = band.YSize
    for i in range(0, xsize, tile_size_x):
        for j in range(0, ysize, tile_size_y):
            com_string = "gdal_translate -of GTIFF -srcwin " + str(i)+ ", " + str(j) + ", " + str(tile_size_x) + ", " + str(tile_size_y) + " " + str(world_shp) + str(input_name) + " " + str(rasterout) + str(output_filename) + str(i) + "_" + str(j) + ".tif"
            os.system(com_string)
            rst = GDALRaster(world_shp + str(output_filename) + str(i) + "_" + str(j) + ".tif" , write=True)
            ele = maxElevation(tile = rst)
            ele.save()

latlon_to_pixal_Converter_specs=[
        ('pixelX', int64), 
        ('pixelY', int64), 
        ('latitude', float64), 
        ('longitude', float64), 
]





@jitclass(latlon_to_pixal_Converter_specs)
class jit_latlon_to_pixal_Converter():

    def __init__(self):
        pass

    def ClipByRange(self,n, range):
        return n % range

    def Clip(self,n, minValue, maxValue):
        return min(max(n, minValue), maxValue)

    def PixelXYToLatLongOSM(self,pixelX,pixelY,zoomLevel):
        mapSize = math.pow(2, zoomLevel) * 512
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

    
class latlon_to_pixal_Converter():

    def __init__(self):
        pass

    def ClipByRange(self,n, range):
        return n % range

    def Clip(self,n, minValue, maxValue):
        return min(max(n, minValue), maxValue)

    def PixelXYToLatLongOSM(self,pixelX,pixelY,zoomLevel):
        mapSize = math.pow(2, zoomLevel) * 512
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
