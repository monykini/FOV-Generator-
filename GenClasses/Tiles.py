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
        square_4326 = self.userMarker.get_square_4326()
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

    def conver_raster_tiles(self):
        if len(self.areaArray) > 0 :
            return self.areaArray

        total_tiles_matrix = self.get_tiles()
        filled_tiles_matrix = []
        f = open("myfile1.txt", "w")

        for t in total_tiles_matrix:
                temp=[]
                for y in t:
                        req = f'https://api.mapbox.com/v4/mapbox.terrain-rgb/15/{y[0]}/{y[1]}@2x.pngraw?access_token=pk.eyJ1IjoiY29zbW9ib2l5IiwiYSI6ImNrNHN0dmwzZjBwMnkzbHFkM3pvaTBybDQifQ.pfeEvOIWJc60mdHtn8_uAQ'
                        print(req)
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
                                        lat,lon =  self.converter.PixelXYToLatLongOSM(x_pixal_world,y_pixal_world,15)
                                        color = filled_tiles_matrix[x][y][i][j]
                                        maerc_lat,maerc_lon = transformer.transform(lat, lon)
                                        height = -10000 + ((color[0] * 256 * 256 + color[1] * 256 + color[2]) * 0.1)
                                        temp2.append({'lat':lat,'lon':lon,'Mercator':[maerc_lat,maerc_lon] , 'color':color ,'world_pixal_X':x_pixal_world,'world_pixal_Y':y_pixal_world , 'pixal_X':x_pixal,'pixal_Y':y_pixal,'height':height})
                                        if Point(maerc_lat,maerc_lon).within(Polygon(self.userMarker.square)):
                                                data = Points([lat,lon], [maerc_lat,maerc_lon] , [x_pixal,y_pixal] , [x_pixal_world,y_pixal_world] , height , color)
                                                flat_array_cords_tiles_matrix.append(data)
                                                f.write(f'{lat},{lon},{[x_pixal,y_pixal]},{color}\n')
                                pixals_per_tile.append(temp2)
                        temp.append(pixals_per_tile)
                cords_tiles_matrix.append(pixals_per_tile)

        self.areaArray = flat_array_cords_tiles_matrix
        return flat_array_cords_tiles_matrix




class latlon_to_pixal_Converter():

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