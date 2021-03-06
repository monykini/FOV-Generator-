from django.contrib.gis import geos


from generator.models import modelPoint,buildingData,obstructions
from .Exceptions import NotEnoughPoints

import shapely
import json
from statistics import stdev , mean
from shapely.geometry import Point, Polygon, LineString
import numpy as np
from pyproj import Transformer
from sklearn import decomposition
from sklearn.cluster import MeanShift
from scipy import stats
from scipy.spatial import ConvexHull as sciConvexHull
import math
from numba import jit , njit
from sympy import symbols
import time

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

class flatSurface():
    def __init__(self,points,hexa):
        self.sides=[]
        self.points = points
        self.insidePoints=[]
        self.modeHeight=0
        self.area=[]
        self.center = 0
        self.center_wsg = 0
        self.hexa=hexa
        self.fov = None
    
    def get_area_flat_surface(self,transformer):
            self.sides = [ i.mac_latlon for i in self.points ]
            polygon = shapely.geometry.Polygon(self.sides)
            self.area = polygon.area
            self.center= list(polygon.centroid.coords)
            self.center = list(self.center[0])
            # transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
            x,y = transformer.transform(self.center[0],self.center[1])
            self.center_wsg =[x,y]
            heights=[]
            for p in self.insidePoints:
                heights.append(p.height)
            self.modeHeight=stats.mode(heights)[0]
    
    def get_sides_4326(self):
        return [ i.latlon for i in self.points ]

    def get_sides_mac(self):
        return [ i.mac_latlon for i in self.points ]
        

class Hexa():
    """
    Hexa(center)

    methods:- \n
    get_maxHeight(self)\n
    get_avgHeight(self)\n
    create_hexagon(self)\n
    get_sides_4326(self)\n
    dertmine_surfaces(self,scanner,points_accessed,falt,x,y,flat)\n
    beta_flatness(self)\n
    create_cube(self,points , checkNmber = None)\n
    """


    def __init__(self,center,**kwargs):
        self.sides = [] #polygon
        self.points = [] 
        self.flat = 0
        self.center = center
        self.triangles = [] #list of triangles
        self.sideLength = 28.868
        if kwargs.get('sideLength',False):
            self.sideLength = kwargs.get('sideLength')
        self.x = 0 
        self.y = 0
        self.cube=[]
        self.side_4326 = [] #polygon
        self.id=None
        self.falt_sufrace=[] # may get deprecative
        self.falt_sufrace_points=[]
        self.falt_sufrace_allPoints=[]

        for key, value in kwargs.items():
            if key == 'x':
                self.x = value
            elif key == 'y':
                self.y = value
        
        self.create_hexagon()
        

    def create_cube(self,points):
        """
        this function create a matrix repesentation of the points to
        understand the relative heights of the points

        create_cube(points)

        returns matrix , min_total_x(minmum x value) , min_total_y(minmum y value) , min_total_z(minmum z value) ,max_x,max_y,max_z

        """
        x,y,z=[],[],[]
        
        for data in points:
            x.append(data.world_pixal_xy[0])
            y.append(data.world_pixal_xy[1])
            z.append(data.height)

        min_total_x , min_total_y , min_total_z = min(x),min(y),int(max(z))
        
        min_x,min_y,min_z,max_x,max_y,max_z=int(min(x)-min(x)),int(min(y)-min(y)),int(min(z)-min(z)),int(max(x)-min(x)),int(max(y)-min(y)),int((max(z))-(min(z)))
        
        cube = np.full((max_z+1, max_x+1,max_y+1 ),-1)
        cube[...] = -1

        for data in points:
            cube[int((data.height)-(min(z)))][int(data.world_pixal_xy[0]-min(x))][int(data.world_pixal_xy[1]-min(y))]=1
        
        return cube , min_total_x , min_total_y , min_total_z ,max_x ,max_y ,max_z

        
    def beta_flatness(self):
        if len(self.points) < 10:
            return
            raise NotEnoughPoints

        cube , min_total_x , min_total_y , min_total_z ,max_x,max_y,max_z = self.create_cube(self.points)

        if type(cube)== type(0):
            return

        scanner =np.full((max_x+1,max_y+1), -1)
        
        for i in range(max_x+1):
            for j in range(max_y+1):
                for z in range(max_z, -1, -1):
                    if cube[z][i][j] >= 1:
                        scanner[i][j] = z
                        break

        points_accessed = []
        
        falt_areas = []
        
        for x in range(len(scanner)):
            for y in range(len(scanner[x])):
                if [x,y] not in points_accessed:
                    flat=[]
                    self.dertmine_surfaces(scanner,points_accessed,x,y,flat)
                    if len(flat) > 1:
                        falt_areas.append(flat)
        
        flat_surface_points=[]
        
        for flat in falt_areas:
            flat_points=[]
            for p in flat:
                for poi in self.points:
                    if poi.world_pixal_xy == [p[0]+min_total_x,p[1]+min_total_y]:
                        flat_points.append(poi)
            flat_surface_points.append(flat_points)
        
        self.cube = cube
        self.falt_sufrace = falt_areas
        self.falt_sufrace_points = flat_surface_points
        

        self.falt_sufrace_points,self.falt_sufrace_allPoints = self.create_borders(flat_surface_points)

    
    def create_borders(self,points):
        flat_surface_polygons=[]
        falt_sufrace_allPoints=[]

        for ch in points:
            cHull = []
            for data in ch:
                cHull.append([data.world_pixal_xy[0],data.world_pixal_xy[1]])

            if (len(cHull) > 2):
                try:
                    hull = sciConvexHull(cHull)
                    polygon = []
                    for p in hull.vertices:
                            polygon.append(ch[p])
                    flat_surface_polygons.append(polygon)
                    falt_sufrace_allPoints.append(ch)
                except:
                    pass
        
        return  flat_surface_polygons , falt_sufrace_allPoints


    def dertmine_surfaces(self,scanner,points_accessed,x,y,flat):
        checks = 0
        #check left point
        if([x,y] not in points_accessed and scanner[x][y] != -1):
            points_accessed.append([x,y])
            if(x-1 >= 0):
                if  abs(scanner[x][y] - scanner[x-1][y]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,x-1,y,flat)
            else:
                checks+=1
            #check right point
            if(x+1 < len(scanner)):
                if  abs(scanner[x][y] - scanner[x+1][y]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,x+1,y,flat)
            else:
                checks+=1 
            #check bottom point
            if( y+1 < len(scanner[x])):
                if  abs(scanner[x][y] - scanner[x][y+1]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,x,y+1,flat)
            else:
                checks+=1 

            #check top point

            if( y-1 >= 0):
                if  abs(scanner[x][y] - scanner[x][y-1]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,x,y-1,flat)
            else:
                checks+=1 

        if checks>=1 :
            flat.append([x,y])

        return

    def get_maxHeight(self):
        heights= []
        for p in self.points:
                heights.append(p.height)
        if len(heights) >= 1:
            return round(max(heights),2)
        return 0

    def get_avgHeight(self):
        heights = []
        for p in self.points:
                heights.append(p.height)
        if len(heights) >= 1:
            return round(sum(heights) / len(heights),2) 
        return 0

    def create_hexagon(self):
                """
                Creates a hexagon centered on (x, y)
                :param l: length of the hexagon's edge
                :param x: x-coordinate of the hexagon's center
                :param y: y-coordinate of the hexagon's center
                :return: The polygon containing the hexagon's coordinates
                """
                if self.sides == []:
                    c = [[self.center[0] + math.cos(math.radians(angle)) * self.sideLength, self.center[1] + math.sin(math.radians(angle)) * self.sideLength] for angle in range(0, 360, 60)]
                    self.sides = Polygon(c)
                return self.sides

    def get_sides_4326(self,*args,**kwargs):
        if self.side_4326 != []:
            return self.side_4326 
        if self.sides == []:
            self.create_hexagon()
        if kwargs.get('transformer',False):
            transformer = kwargs.get('transformer')
        else:
            transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        polygon_4326 = []
        for p in list(self.sides.exterior.coords):
            x,y = transformer.transform(p[0], p[1])
            polygon_4326.append([x,y])
        self.side_4326 = Polygon(polygon_4326)
        return self.side_4326 

        






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
        self.height = 0
        self.id = None
    
    def get_square(self):
        if self.square == 0:
            transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
            x2,y2 = transformer.transform(self.latlon[0], self.latlon[1])
            point = shapely.geometry.Point(x2,y2)
            #anti-clock wise top - right corner
            og_square = point.buffer(self.area , cap_style=3)
            self.square = og_square
            return self.square
        else:
            return self.square
    
    def get_latlonMac(self , *args,**kwargs):
        if kwargs.get('transformer',None) != None:
            transformer = kwargs.get('transformer',None)
        else:
            transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        lat,lon = transformer.transform(self.latlon[0], self.latlon[1])
        return [lat,lon]

    def get_square_4326(self, *args,**kwargs):
        if self.square == 0 :
            self.get_square()

        if kwargs.get('transformer',None) != None:
            transformer = kwargs.get('transformer',None)
        else:
            transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        square_4326 = []
        for p in list(self.square.exterior.coords):
            x,y = transformer.transform(p[0], p[1])
            square_4326.append([x,y])
        return shapely.geometry.Polygon(square_4326)

    def get_weather(self):
        pass




class FOV():
    """
    class FOV()
    methods:\n
    1.create_fov(hexa_center , user_point)\n
    both needs to be in epsg:3857
    """

    def __init__(self):
        self.visibility = None
        self.view_area = None
        self.start = None
        self.area = 0
        self.hexas = []
        self.angle = 45
        self.height = 0
        self.obstrcution = 0
        self.sign=0
        self.center = False
    

    def create_fov(self , hexa_center , userPoint):
        self.start = hexa_center
        raw_hight_vector = [hexa_center[0]-userPoint[0] ,hexa_center[1]-userPoint[1]]

        height_vector = [abs(hexa_center[0]-userPoint[0]) ,abs(hexa_center[1]-userPoint[1])]
        height_value = math.sqrt(math.pow(hexa_center[0]-userPoint[0],2)+math.pow(hexa_center[1]-userPoint[1],2))

        self.height = height_value 

        hypo = height_value / math.cos((self.angle/2)*(math.pi/180))

        length_new_vector =abs( hypo * math.sin((self.angle/2)*(math.pi/180)))

        height_normal = [height_vector[0]/height_value , height_vector[1]/height_value]

        matrix_height_normal = [[height_normal[0]],[height_normal[1]]]
        matix_clock_wise = [[0 , -1],[1 , 0]]
        matix_anticlock_wise = [[0 , 1],[-1 , 0]]

        vector1 = ((np.matmul(matix_clock_wise,matrix_height_normal)*length_new_vector).ravel()).tolist()
        vector2 = ((np.matmul(matix_anticlock_wise,matrix_height_normal)*length_new_vector).ravel()).tolist()

        if (raw_hight_vector[0] * raw_hight_vector[1]) > 0 :
            vertices = [hexa_center , [userPoint[0]+vector1[0] , userPoint[1]+vector1[1]],[userPoint[0]+vector2[0] , userPoint[1]+vector2[1]]]
            self.sign=1
        else:
            vertices = [hexa_center , [userPoint[0]+vector1[0] , userPoint[1]+vector2[1]],[userPoint[0]+vector2[0] , userPoint[1]+vector1[1]]]
        
        self.view_area = vertices
        polygon = shapely.geometry.Polygon(self.view_area)
        self.area = polygon.area
        # self.get_fov_4326(transformer)


    def create_cube(self,points,checkNmber=None):
        x,y,z=[],[],[]
        if len(points) < 5 and checkNmber != None:
            return None , None , None , None ,None,None,None
        for data in points:
            x.append(data.world_pixal_xy[0])
            y.append(data.world_pixal_xy[1])
            z.append(data.height)
        min_total_x , min_total_y , min_total_z = min(x),min(y),int(max(z))
        min_x,min_y,min_z,max_x,max_y,max_z=int(min(x)-min(x)),int(min(y)-min(y)),int(min(z)-min(z)),int(max(x)-min(x)),int(max(y)-min(y)),int(max(z)-min(z))
        cube = np.full((max_z+1, max_x+1,max_y+1 ),-1)
        cube[...] = -1
        for data in points:
            cube[int((data.height)-min(z))][int(data.world_pixal_xy[0]-min(x))][int(data.world_pixal_xy[1]-min(y))]=1
        return cube , min_total_x , min_total_y , min_total_z ,max_x,max_y,max_z


    def get_fov_4326(self,transformer):
        if self.view_area == None :
            return None
        
        # transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        square_4326 = []
        for p in range(len(self.view_area)):
            x,y = transformer.transform(self.view_area[p][0], self.view_area[p][1])
            square_4326.append([x,y])
        return square_4326


  

class hexaGridnoSave():
        """
        creates a hexagrid \n
        hexaGrid(userMarker)
        methods: \n
        calculate_grid(self) :- creates a hexagrid
        Mapper(self,tilesArray) :- takes tilesArray form tile_gather class and maps each point to respective hexa in grid
        """
        def __init__(self):
                self.hexas = []
                self.sideLength = 4
                # self.flat_surfaces = []
                # self.calculate_grid()

        def calculate_grid(self,x_max,x_min,y_max,y_min):
                """
                returns an array of Points describing hexagons centers that are inside the given bounding_box \n
                :return: The hexagon grid \n
                """
                grid = []

                v_step = math.sqrt(3) * self.sideLength
                h_step = 1.5 * self.sideLength


                # bbox = list(self.userMarker.get_square().exterior.coords)

                # x_min = bbox[3][0]
                # x_max = bbox[1][0]
                # y_min = bbox[1][1]
                # y_max = bbox[3][1]


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
                transformer = Transformer.from_crs("epsg:3857", "epsg:4326")
                x = 0
                while c_x < h_end:
                        y = 0
                        while c_y < v_end:
                                c_x1, c_y1=transformer.transform(c_x, c_y)
                                hexa = Hexa([c_x, c_y],x=x,y=y,sideLength=self.sideLength)
                                # macpoint = geos.Point(c_y, c_x)
                                # wsg48point = geos.Point(c_y1, c_x1)
                                # wsg48Polygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(hexa.get_sides_4326().exterior.coords)]))
                                # macpolygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(hexa.create_hexagon().exterior.coords)]))
                                grid.append(hexa)
                                c_y += v_step
                                y+=1
                        c_x += h_step
                        c_y = v_start_array[v_start_idx]
                        v_start_idx = (v_start_idx + 1) % 2
                        x+=1
                self.hexas = grid
                return grid