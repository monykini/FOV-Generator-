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




def GetExtent(ds):
        """ Return list of corner coordinates from a gdal Dataset """
        xmin, xpixel, _, ymax, _, ypixel = ds.GetGeoTransform()
        width, height = ds.RasterXSize, ds.RasterYSize
        xmax = xmin + width * xpixel
        ymin = ymax + height * ypixel

        return (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)

def ReprojectCoords(coords,src_srs,tgt_srs):

        trans_coords=[]
        transform = osr.CoordinateTransformation( src_srs, tgt_srs)
        for x,y in coords:
                x,y,z = transform.TransformPoint(x,y)
                trans_coords.append([x,y])
        return trans_coords


def get_raster_bounds(filename = None):
        if filename == None:
                raster=r'data.tif'
        else:
                raster = filename
        print(raster)
        ds=gdal.Open(raster)
        print(ds)
        ext=GetExtent(ds)
        print(ext)
        print(ds.RasterCount)
        src_srs=osr.SpatialReference()
        src_srs.ImportFromWkt(ds.GetProjection())
        #tgt_srs=osr.SpatialReference()
        #tgt_srs.ImportFromEPSG(4326)
        print(src_srs)
        tgt_srs = src_srs.CloneGeogCS()
        print(tgt_srs)
        geo_ext=ReprojectCoords(ext, src_srs, tgt_srs)

        return geo_ext



def pixel(dx,dy):
    px = file.GetGeoTransform()[0]
    py = file.GetGeoTransform()[3]
    rx = file.GetGeoTransform()[1]
    ry = file.GetGeoTransform()[5]
    x = dx/rx + px
    y = dy/ry + py
    return x,y

def georefrence():
        src_filename ='9650-12314.tif'
        dst_filename = 'destination_ref.tif'

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
        gt = [-7916400, 100, 0, 5210940, 0, -100]

        # Set location
        dst_ds.SetGeoTransform(gt)

        # Get raster projection
        epsg = 3857
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        dest_wkt = srs.ExportToWkt()

        # Set projection
        dst_ds.SetProjection(dest_wkt)

        # Close files
        dst_ds = None
        src_ds = None