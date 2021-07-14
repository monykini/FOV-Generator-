import json
import os
import mercantile
from generator.models import modelPoint, modelUserMarker,buildingData
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
from FOV import settings as st
import requests
from PIL import Image
from io import BytesIO


world_shp = f'buidlingsData/elevation/'
input_name ='30n060e_20101117_gmted_max075.tif'
rasterout = 'buidlingsData/elevation/'
output_filename = 'tile_'

tile_size_x = 512
tile_size_y = 512



# def run(verbose=True):
def get_tiles(coords):
        tiles = []
        square_4326 = coords
        for p in square_4326:
                print(p[1],p[0])
                mercent = mercantile.tile(p[1],p[0],15)
                tiles.append([mercent.x,mercent.y])
        

        x_matrix =  [ p[1] for p in tiles ]
        y_matrix = [p[0] for p in tiles]
        print(x_matrix)
        print(y_matrix)
        x_matrix_max , x_matrix_min = max(x_matrix) , min(x_matrix)
        y_matrix_max , y_matrix_min = max(y_matrix) , min(y_matrix)
        print(x_matrix_max , x_matrix_min)
        print(y_matrix_max , y_matrix_min)
        total_x_axis_tiles = x_matrix_max-x_matrix_min+1
        total_y_axis_tiles = y_matrix_max-y_matrix_min+1

        top_left_tile = tiles[0]
        total_tiles_matrix=[]
        for x in range(total_x_axis_tiles):
                temp=[]
                for y in range(total_y_axis_tiles):
                        temp.append([top_left_tile[0]+y,top_left_tile[1]+x])
                total_tiles_matrix.append(temp)

        total_tiles_matrix = total_tiles_matrix[::-1]
        return total_tiles_matrix


def get_data():
        if os.path.exists('MLData/') == False:
                os.mkdir('MLData/')
        userRasterPath = f"MLData/"
        converter = latlon_to_pixal_Converter()
        newyork_bbox= geos.Polygon(st.newyork_bbox_square)
        polygon_list = [list(cod)[::-1] for cod in newyork_bbox.coords[0]]
        Tiles = get_tiles(polygon_list)
        for tileRow in Tiles:
                for t in tileRow:
                        print(t[0],t[1],'lmao')
                        req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{t[0]}/{t[1]}@2x.png256?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                        req = requests.get(req)
                        image = Image.open(BytesIO(req.content))
                        data = np.asarray(image)
                        x_pixal_world = (0+(512*t[0]))
                        y_pixal_world = (0+(512*t[1]))
                        upperLeftLat,upperLeftLon =  converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                        x_pixal_world = (511+(512*t[0]))
                        y_pixal_world = (511+(512*t[1]))
                        lowerRightLat,lowerRightLon =  converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                        maxLat,minLat = max([upperLeftLat,lowerRightLat]),min([upperLeftLat,lowerRightLat])
                        maxLon,minLon = max([upperLeftLon,lowerRightLon]),min([upperLeftLon,lowerRightLon])
                        poly = geos.Polygon(((maxLon,maxLat),(maxLon,minLat),(minLon,maxLat),(minLon,minLat),(maxLon,maxLat)))
                        shapelypoly = shapely.geometry.Polygon([(maxLon,maxLat),(maxLon,minLat),(minLon,maxLat),(minLon,minLat),(maxLon,maxLat)]).buffer(0)
                        buildings = []
                        geojson = {"type": "FeatureCollection","crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }} ,"features": [] }
                        if buildingData.objects.filter(geom__intersects = poly).exists():
                                for MB in buildingData.objects.filter(geom__intersects = poly):
                                        buildingPloygon = []
                                        print(MB.geom.coords)
                                        for MBpoly in MB.geom.coords:
                                                print(MBpoly[0])
                                                temp = shapely.geometry.Polygon(list(MBpoly[0]))
                                                buildingPloygon.append(temp.buffer(0))
                                        buildingsPolygon = shapely.geometry.MultiPolygon(buildingPloygon)
                                        buildingsPolygon = buildingsPolygon.buffer(0)
                                        print(shapelypoly.is_valid)
                                        print(buildingsPolygon.is_valid)
                                        clipped = buildingsPolygon.intersection(shapelypoly)
                                        print(clipped)
                                        if clipped.geom_type == 'Polygon':
                                                try:
                                                        print(list(clipped.exterior.coords))
                                                except:
                                                        print(list(clipped.geoms))
                                                feature = { "type": "Feature","geometry": { "type": "Polygon", "coordinates":[]}}
                                                feature['coordinates'] = [ list(l) for l in list(clipped.exterior.coords)]
                                                geojson['features'].append(feature)
                                        elif clipped.geom_type == 'MultiPolygon' :
                                                for geo in list(clipped.geoms):
                                                        print(list(geo.exterior.coords))
                                                        feature = { "type": "Feature","geometry": { "type": "Polygon", "coordinates":[]}}
                                                        feature['coordinates'] = [ list(l) for l in list(geo.exterior.coords)]
                                                        geojson['features'].append(feature)
                                        else:
                                                for geo in list(clipped):
                                                        print(list(geo.exterior.coords))
                                                        feature = { "type": "Feature","geometry": { "type": "Polygon", "coordinates":[]}}
                                                        feature['coordinates'] = [ list(l) for l in list(geo.exterior.coords)]
                                                        geojson['features'].append(feature)
                        
                        file = open(f"{userRasterPath}{t[0]}-{t[1]}.geojson", "w")
                        file.write(json.dumps(geojson))
                        file.close()
                        break
                # break






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
        

