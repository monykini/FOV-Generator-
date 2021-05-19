import json
import os
import mercantile
from generator.models import modelPoint
from django.contrib.gis.gdal import GDALRaster
import numpy as np
from shapely.geometry import Point
from numba import jit , njit
from numba import int64, float64
from numba.experimental import jitclass
import math
import time
import shapely
from osgeo import gdal,ogr,osr
import rasterio
import rasterio.features

world_shp = f'buidlingsData/elevation/'
input_name ='30n060e_20101117_gmted_max075.tif'
rasterout = 'buidlingsData/elevation/'
output_filename = 'tile_'

tile_size_x = 512
tile_size_y = 512



# def run(verbose=True):


def create_fov(hexa_center , userPoint ,angle):
        raw_hight_vector = [hexa_center[0]-userPoint[0] ,hexa_center[1]-userPoint[1]]
        height_vector = [abs(hexa_center[0]-userPoint[0]) ,abs(hexa_center[1]-userPoint[1])]
        
        height_value = math.sqrt(math.pow(hexa_center[0]-userPoint[0],2)+math.pow(hexa_center[1]-userPoint[1],2))
        hypo = height_value / math.cos((angle/2)*(math.pi/180))
        length_new_vector =abs( hypo * math.sin((angle/2)*(math.pi/180)))
        height_normal = [height_vector[0]/height_value , height_vector[1]/height_value]
        cos_90 = 0
        sin_90 = 1
        matrix_height_normal = [[height_normal[0]],[height_normal[1]]]
        print(matrix_height_normal)
        
        matix_clock_wise = [[0 , -1],[1 , 0]]
        matix_anticlock_wise = [[0 , 1],[-1 , 0]]
        print((np.matmul(matix_clock_wise,matrix_height_normal)*length_new_vector).ravel())
        print((np.matmul(matix_anticlock_wise,matrix_height_normal)*length_new_vector).ravel())
        vector1 = ((np.matmul(matix_clock_wise,matrix_height_normal)*length_new_vector).ravel()).tolist()
        vector2 = ((np.matmul(matix_anticlock_wise,matrix_height_normal)*length_new_vector).ravel()).tolist()
        vertices = [hexa_center , [userPoint[0]+vector1[0] , userPoint[1]+vector2[1]],[userPoint[0]+vector2[0] , userPoint[1]+vector1[1]]]
        if raw_hight_vector[0] > 0 and raw_hight_vector[1] > 0:
                vertices[1][1] = -(vertices[1][1]) 
                vertices[2][1] = -(vertices[2][1]) 
        print(vertices)




def GetExtent():
        with rasterio.open('userRasters/usama.khan/output.tif') as src:
                crs = src.crs
                src_band = src.read(1)
                # Keep track of unique pixel values in the input band
                unique_values = [255]
                # Polygonize with Rasterio. `shapes()` returns an iterable
                # of (geom, value) as tuples
                shapes = list(rasterio.features.shapes(src_band, transform=src.transform))
        print(shapes)
