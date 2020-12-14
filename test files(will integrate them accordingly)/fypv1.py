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
import threading
from statistics import stdev 
#Do not apply an operation to the result of another operation
#Write a new operation that combines the two operations.


class area_calculate():
        def __init__(self, lat, lon , area):
                self.lat = 33.64013671875
                self.lon = 73.0455032
                self.hexagon_centers=[]
                self.area_data=[]
                self.area = area

        def ClipByRange(self,n, range):
                return n % range

        def Clip(self,n, minValue, maxValue):
                return min(max(n, minValue), maxValue)

        def PixelXYToLatLongOSM(self,pixelX,pixelY,zoomLevel):

                mapSize = math.pow(2, zoomLevel) * 256
                tileX = math.trunc(pixelX / 256)
                tileY = math.trunc(pixelY / 256)

                n = math.pi - ((2.0 * math.pi * (self.ClipByRange(pixelY, mapSize - 1) / 256)) / math.pow(2.0, zoomLevel))

                longitude = ((self.ClipByRange(pixelX, mapSize - 1) / 256) / math.pow(2.0, zoomLevel) * 360.0) - 180.0
                latitude = (180.0 / math.pi * math.atan(math.sinh(n)))
                # print(latitude,longitude)
                return latitude,longitude


        def get_square(self):
                transformer = Transformer.from_crs("epsg:4326", "epsg:3857")

                # lon first lat last
                x2,y2 = transformer.transform(self.lat, self.lon)
                point = shapely.geometry.Point(x2,y2)
                
                #anti-clock wise top - right corner
                og_square = point.buffer(self.area, cap_style=3)
                return og_square


        def get_area_data(self):
                og_square = self.get_square()
                square = list(og_square.exterior.coords)
                transformer = Transformer.from_crs("epsg:3857","epsg:4326")
                square_4326 = []
                for p in range(len(square)-1):
                        x,y = transformer.transform(square[p][0], square[p][1])
                        square_4326.append([x,y])
                tiles = []
                for p in square_4326:
                        mercent = mercantile.tile(p[1],p[0],15)
                        print(mercent)
                        tiles.append([mercent.x,mercent.y])

                #-----y-axis is first------------------------
                # print(tiles,"tiles")
                total_x_axis_tiles = tiles[1][1]-tiles[0][1]+1
                total_y_axis_tiles = tiles[1][0]-tiles[2][0]+1
                # print(total_x_axis_tiles,total_y_axis_tiles)
                #------here the corner are reset to proper form------
                top_left_tile = tiles[0]
                total_tiles_matrix=[]
                for x in range(total_x_axis_tiles):
                        temp=[]
                        for y in range(total_y_axis_tiles):
                                temp.append([top_left_tile[0]-x,top_left_tile[1]+y])
                        total_tiles_matrix.append(temp)

                total_tiles_matrix = total_tiles_matrix[::-1]
                #print(np.array(total_tiles_matrix))
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
                flat_array_cords_tiles_matrix=[]
                for x in range(len(total_tiles_matrix)):
                        temp = []
                        for y in range(len(total_tiles_matrix[x])):
                                pixals_per_tile= []
                                for i in range(256):
                                        temp2=[]
                                        for j in range(256):
                                                x_pixal_world = (i+(256*total_tiles_matrix[x][y][0]))
                                                y_pixal_world = (j+(256*total_tiles_matrix[x][y][1]))
                                                x_pixal=i+(x*256)
                                                y_pixal=j+(y*256)
                                                lat,lon =  self.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                                color = filled_tiles_matrix[x][y][i][j]
                                                maerc_lat,maerc_lon = transformer.transform(lat, lon)
                                                height = -10000 + ((color[1] * 256 * 256 + color[2] * 256 + color[3]) * 0.1)
                                                data={"world_xy_pixal":[x_pixal_world,y_pixal_world],'lat/lon(inorder)':[lat,lon],"pixal_x_y":[x_pixal,y_pixal],'color':color , 'Mercator':[maerc_lat,maerc_lon] , 'elevation(meter)':height}
                                                flat_array_cords_tiles_matrix.append(data)
                                                temp2.append({'lat':lat,'lon':lon,'Mercator':[maerc_lat,maerc_lon] , 'color':color ,'world_pixal_X':x_pixal_world,'world_pixal_Y':y_pixal_world , 'pixal_X':x_pixal,'pixal_Y':y_pixal,'height':height})
                                                f.write(f'{lat},{lon},{[x_pixal,y_pixal]}\n')
                                        pixals_per_tile.append(temp2)
                                temp.append(pixals_per_tile)
                        cords_tiles_matrix.append(pixals_per_tile)

                return flat_array_cords_tiles_matrix


        def assign_points(self,poly):
                temp=[]
                for data in self.area_data:
                        if Point(data['Mercator']).within(poly):
                                temp.append(data)
                return temp

        def pointy_hex_corner(self,center, size, i):
                angle_deg = 60 * i - 30
                angle_rad = math.pi / 180 * angle_deg
                return Point(center[0] + size * math.cos(angle_rad),center[1] + size * math.sin(angle_rad))


        def create_hexgrid(self,bbox, side):
                """
                returns an array of Points describing hexagons centers that are inside the given bounding_box
                :param bbox: The containing bounding box. The bbox coordinate should be in Webmercator.
                :param side: The size of the hexagons'
                :return: The hexagon grid
                """
                grid = []

                v_step = math.sqrt(3) * side
                h_step = 1.5 * side

                x_min = bbox[3][0]
                x_max = bbox[1][0]
                y_min = bbox[1][1]
                y_max = bbox[3][1]
                # print(x_min , x_max , y_max , y_min)

                h_skip = math.ceil(x_min / h_step) - 1
                h_start = h_skip * h_step

                v_skip = math.ceil(y_min / v_step) - 1
                v_start = v_skip * v_step

                h_end = x_max + h_step
                v_end = y_max + v_step

                if v_start - (v_step / 2.0) < y_min:
                        v_start_array = [v_start + (v_step / 2.0), v_start]
                else:
                        v_start_array = [v_start - (v_step / 2.0), v_start]

                v_start_idx = int(abs(h_skip) % 2)

                c_x = h_start
                c_y = v_start_array[v_start_idx]
                v_start_idx = (v_start_idx + 1) % 2
                # transformer = Transformer.from_crs("epsg:3857", "epsg:4326")
                while c_x < h_end:
                        while c_y < v_end:
                                # c_x1, c_y1=transformer.transform(c_x, c_y)
                                grid.append([c_x, c_y])
                                c_y += v_step
                        c_x += h_step
                        c_y = v_start_array[v_start_idx]
                        v_start_idx = (v_start_idx + 1) % 2
                
                return grid

        def create_hexagon(self,l, x, y):
                """
                Create a hexagon centered on (x, y)
                :param l: length of the hexagon's edge
                :param x: x-coordinate of the hexagon's center
                :param y: y-coordinate of the hexagon's center
                :return: The polygon containing the hexagon's coordinates
                """
                c = [[x + math.cos(math.radians(angle)) * l, y + math.sin(math.radians(angle)) * l] for angle in range(0, 360, 60)]
                for p in list(Polygon(c).exterior.coords):
                        transformer = Transformer.from_crs("epsg:3857", "epsg:4326")
                        x1,y1 = transformer.transform(p[0], p[1])
                        print(f"{x1},{y1}")
                return Polygon(c)

        def create_hexagons(self):
                self.area_data = self.get_area_data()
                square =  self.get_square()
                grid = self.create_hexgrid(list(square.exterior.coords), 28.868)
                self.hexagon_centers = grid
                # w = math.sqrt(3) * 28.868
                # h = 2 * 28.868
                # starting_point  = [list(square.exterior.coords)[3][0] + w,list(square.exterior.coords)[3][1] - h]
                # self.get_center(starting_point,square,w,h)
                # r=28.8675
                # h = (2/(3**0.5))*r
                # print(self.hexagon_centers)
                complete_hexagons = []
                for point in self.hexagon_centers:
                        dic = {'center':point,'hexa_polygon':self.create_hexagon(28.868,point[0],point[1])}
                        temp=[]
                        transformer = Transformer.from_crs("epsg:3857", "epsg:4326")
                        for point in list(dic['hexa_polygon'].exterior.coords):
                                x,y = transformer.transform(point[0], point[1])
                                temp.append([x,y])
                        dic['hexa_polygon_cord']=Polygon(temp) 
                        complete_hexagons.append(dic)
                complete_hexagons = pd.DataFrame(complete_hexagons)
                complete_hexagons['contain_points']=complete_hexagons['hexa_polygon']
                complete_hexagons['contain_points']=complete_hexagons['contain_points'].apply(self.assign_points)
                return complete_hexagons
        

        def flat_suface(self,points):
                heights = []
                for p in points:
                        heights.append(p['elevation(meter)'])
                
                if len(heights) >= 2:
                        return stdev(heights)
                return 0
                        
        def get_flat_surfaces(self,complete_hexagons):
                complete_hexagons['flat%'] = complete_hexagons['contain_points']
                complete_hexagons['flat%'] = complete_hexagons['flat%'].apply(self.flat_suface)
                return complete_hexagons












def main():
    area  = area_calculate(33.64013671875,73.0455032,200)
    hexagons = area.create_hexagons()
#   print(hexagons.to_string())
    hexagons = area.get_flat_surfaces(hexagons)

if __name__ == "__main__":
    main()










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
