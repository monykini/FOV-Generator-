from statistics import stdev , mean
from pyproj import Transformer
from shapely.geometry import Point, Polygon, LineString
import shapely
import math



class Points():
    """
    Points(latlon, mac_latlon , pixal_xy , world_pixal_xy , height , color)
    """
    def __init__(self, latlon, mac_latlon , pixal_xy , world_pixal_xy , height , color):
        self.latlon = latlon
        self.mac_latlon = mac_latlon
        self.pixal_xy = pixal_xy
        self.world_pixal_xy = world_pixal_xy
        self.height = height
        self.color = color
        self.sideLength = 28.868

class Triangle():

    def __init__(self,sides):
        self.sides = sides #polygon
        self.points = []
        self.flatness= 0
    



class Hexa():
    """
    Hexa(center)

    methods:- \n
    check_flatness(self)\n
    get_maxHeight(self)\n
    get_avgHeight(self)\n
    create_hexagon(self)\n
    get_sides_4326(self)\n
    """
    def __init__(self,center):
        self.sides = [] #polygon
        self.points = [] 
        self.flat = 0
        self.center = center
        self.triangles = []#list of triangles
        self.obstructs = False
        self.sideLength = 28.868
        
    
    def check_flatness(self):
        if self.triangles == []:
            polygons = []
            sides = list(self.sides.exterior.coords)
            for p in range(len(sides)-1):
                point_1 = []
                point_2 = []
                if(p >= len(sides)-1):
                    point_1 = sides[0]
                    point_2 = sides[p]
                else:
                    point_1 = sides[p]
                    point_2 = sides[p+1]
                # print(point_1)
                polygons.append(Triangle(Polygon([point_1,point_2,self.center])))
            self.triangles = polygons
        print(self.triangles)
        for data in self.points:
            for tri in self.triangles:
                # print(hexa.create_hexagon())
                if Point(data.mac_latlon[0],data.mac_latlon[1]).within(tri.sides):
                        tri.points.append(data)
                        print("pounts" , data.latlon)
        
        accepted=0
        for tri in self.triangles:
            heights = []
            for p in tri.points:
                heights.append(p.height)
            
            if len(heights) >= 2:
                heights_mean = mean(heights)
                deviation = stdev(heights)
                lowerBound = heights_mean - 2*(deviation)
                higherBound = heights_mean + 2*(deviation)
                tri.flatness = (abs(lowerBound - higherBound )/heights_mean) * 100
                print(tri.flatness , lowerBound , higherBound , heights_mean)
                if tri.flatness <= 0.01:
                    accepted += 1
        
        self.flat = accepted/6 * 100

        return self.flat
        
        

        


        

        # heights = []
        # for p in self.points:
        #         heights.append(p['elevation(meter)'])
        


        # if len(heights) >= 2:
        #         heights_mean = mean(heights)
        #         deviation = stdev(heights)
                

    def get_maxHeight(self):
        heights= []
        for p in self.points:
                heights.append(p['elevation(meter)'])
        if len(heights) >= 1:
            return max(heights)
        return 0

    def get_avgHeight(self):
        heights = []
        for p in self.points:
                heights.append(p['elevation(meter)'])
        if len(heights) >= 1:
            return sum(heights) / len(heights) 
        return 0

    def create_hexagon(self):
                """
                Create a hexagon centered on (x, y)
                :param l: length of the hexagon's edge
                :param x: x-coordinate of the hexagon's center
                :param y: y-coordinate of the hexagon's center
                :return: The polygon containing the hexagon's coordinates
                """
                if self.sides == []:
                    c = [[self.center[0] + math.cos(math.radians(angle)) * self.sideLength, self.center[1] + math.sin(math.radians(angle)) * self.sideLength] for angle in range(0, 360, 60)]
                    self.sides = Polygon(c)
                return self.sides

    def get_sides_4326(self):
        if self.sides == []:
            self.create_hexagon()
        transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        polygon_4326 = []
        for p in list(self.sides.exterior.coords):
            x,y = transformer.transform(p[0], p[1])
            polygon_4326.append([x,y])
        return polygon_4326

        






class userMarker():
    """
    Enter latlon in epsg:4326 format\n
    userMarker(latlon)\n
    methods:=\n
    get_square(self)\n
    get_latlonMac(self)\n
    get_square_4326(self)\n
    """
    def __init__(self,latlon,area):
        self.latlon = latlon
        self.area = area
        self.square = 0
    
    def get_square(self):
        if self.square == 0:
            transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
            # lon first lat last
            x2,y2 = transformer.transform(self.latlon[0], self.latlon[1])
            point = shapely.geometry.Point(x2,y2)
            
            #anti-clock wise top - right corner
            og_square = point.buffer(self.area, cap_style=3)
            square = list(og_square.exterior.coords)
            self.square = square
            return self.square
        else:
            return self.square
    
    def get_latlonMac(self):
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        lat,lon = transformer.transform(self.latlon[0], self.latlon[1])
        return [lat,lon]

    def get_square_4326(self):
        if self.square == 0 :
            self.get_square()
        
        transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        square_4326 = []
        for p in range(len(self.square)-1):
            x,y = transformer.transform(self.square[p][0], self.square[p][1])
            square_4326.append([x,y])
        return square_4326
