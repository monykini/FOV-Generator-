import json
import os
import mercantile
from generator.models import modelPoint, modelUserMarker
from GenClasses.Shapes import userMarker
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
from django.contrib.gis import geos
import pandas as pd

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
        Marker = userMarker([-73.96822854362219,40.76470739485811][::-1],200)
        print(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
        wsg48polygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
        points = modelPoint.objects.filter(wsg48Point__intersects = wsg48polygon)

        # driver = gdal.GetDriverByName( 'GTiff' )
        # dst_filename = 'tmp.tif'

        cube = create_cube(points)
        

def create_cube(points):
        x,y,z=[],[],[]
        for data in points:
            x.append(json.loads(data.world_pixal_xy)[0])
            y.append(json.loads(data.world_pixal_xy)[1])
            z.append(data.height)
        min_total_x , min_total_y , min_total_z = min(x),min(y),int(max(z))
        min_x,min_y,min_z,max_x,max_y,max_z=int(min(x)-min(x)),int(min(y)-min(y)),int(min(z)-min(z)),int(max(x)-min(x)),int(max(y)-min(y)),int(max(z)-min(z))
        cube = np.full((max_x+1,max_y+1),-1)
        cube[...] = -1
        for data in points:
            cube[int(json.loads(data.world_pixal_xy)[0]-min(x))][int(json.loads(data.world_pixal_xy)[1]-min(y))]=data.id

        print(cube[0][0])
        origin = [points.get(id =cube[0][0]).macPoint[0],points.get(id =cube[0][0]).macPoint[1]]
        pixal_x = points.get(id =cube[0][0]).macPoint[0] - points.get(id =cube[0][1]).macPoint[0]
        pixal_y = points.get(id =cube[0][0]).macPoint[1] - points.get(id =cube[1][0]).macPoint[1]

        print(origin,pixal_x,pixal_y)
        return cube


def create_raster():
        marker = modelUserMarker.objects.all()[0]
        points = modelPoint.objects.filter(wsg48Point__intersects =marker.wsg48polygon)
        lats = []
        lons = []
        for p in points:
                lons.append(p.macPoint[1])
                lats.append(p.macPoint[0])
        min_lon,min_lat = min(lons),min(lats)
        max_lon,max_lat = max(lons),max(lats)
        total_lon = max_lon - min_lon
        total_lat = max_lat - max_lat

        dictCoods = []
        for l in range(total_lon):
                temp1 = []
                for la in range(total_lat):
                        temp.append([min_lon+(l*2.388657134),min_lat+(la*2.388657134)])
                dictCoods.append(temp)
       

        dict_points=[]
        for p in points:
                temp = {"x":json.loads(p.world_pixal_xy)[0],"y":json.loads(p.world_pixal_xy)[1],"height":p.height}
                dict_points.append(temp)
        df= pd.DataFrame(dict_points)
        df = df.sort_values(["x","y"],ascending=[True,False])
        df.to_csv("df.xyz",index=False,header=None,sep=" ")



def create_raster_beta():
        marker = modelUserMarker.objects.all()[0]
        points = modelPoint.objects.filter(wsg48Point__intersects =marker.wsg48polygon)
        dict_points=[]
        for p in points:
                x = p.macPoint[1]
                y = p.macPoint[0]
                temp = {"x":x,"y":y,"height":p.height}
                dict_points.append(temp)
        df= pd.DataFrame(dict_points)
        df = df.sort_values(["x","y"],ascending=[True,True])
        previous_x = 0
        previous_y = 0 
        dict_points = []
        req_interval  = 2.388657134
        ys = []
        for ID , row in df.iterrows():
                if ID == 0 :
                        previous_y = row["y"]
                        y = row["y"]
                else:
                        difference_y = previous_y - row["y"]
                        if difference_y - req_interval == 0:
                                y = row["y"]
                        else:
                                gap = difference_y - req_interval
                                y = row["y"] + gap
                ys.append(y)
        xs=[]
        df = df.sort_values(["y","x"],ascending=[True,True])
        for ID , row in df.iterrows():
                if ID == 0 :
                        previous_x = row["x"]
                        x = row["x"]
                else:
                        difference_x = previous_x - row["x"]
                        if difference_x - req_interval == 0:
                                x = row["x"]
                        else:
                                gap = difference_x - req_interval
                                x = row["x"] + gap
                xs.append(y)

        df['x'] = xs
        df['y'] = ys

        df.to_csv("uneven.csv",index=False,sep=" ")

        if os.path.exists("dem.tif"):
                os.remove('dem.tif')

        dem = gdal.Translate("dem.tif","uneven.tif",outputSRS = "EPSG:3857")

#         if os.path.exists("uneven.vrt"):
#                 os.remove('uneven.vrt')
        
#         f = open("uneven.vrt","w")
#         f.write("""<OGRVRTDataSource>
#     <OGRVRTLayer name="uneven">
#         <SrcDataSource>uneven.csv</SrcDataSource>
#         <GeometryType>wkbPoint</GeometryType>
#         <GeometryField encoding="PointFromColumns" x="x" y="y" z="height"/>
#     </OGRVRTLayer>
# </OGRVRTDataSource>""")
#         f.close()

        # r = gdal.Rasterize("uneven.tif","uneven.vrt",outputSRS = "EPSG:3857",xRes=2.388657131 , yRes = -2.388657131 , attribute = 'height' , noData = np.nan)
        # # r = None

        # r = gdal.Grid("unevenInt.tif","uneven.vrt",outputSRS = "EPSG:3857")
        # r = None

        
        

