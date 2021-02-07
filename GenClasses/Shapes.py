from statistics import stdev , mean
from pyproj import Transformer
from shapely.geometry import Point, Polygon, LineString
import shapely
import math
from sklearn import decomposition
import numpy as np



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

class Triangle():

    def __init__(self,sides):
        self.sides = sides #polygon
        self.points = []
        self.flatness= 0
    
    def get_sides_4326(self):
        transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        polygon_4326 = []
        for p in list(self.sides.exterior.coords):
            x,y = transformer.transform(p[0], p[1])
            polygon_4326.append([x,y])
        return polygon_4326
    


class flatSurface():
    def __init__(self,points,hexa):
        self.sides=[]
        self.points = points
        self.area=[]
        self.averageHeight=[]
        self.center = 0
        self.hexa=hexa
        self.get_area_flat_surface()
        self.fov = None

    def get_area_flat_surface(self):
            self.sides = [ i.mac_latlon for i in self.points ]
            polygon = shapely.geometry.Polygon(self.sides)
            self.area = polygon.area
            self.center= list(polygon.centroid.coords)
            print(self.area,self.center)
    
    def get_sides_4326(self):
        return [ i.latlon for i in self.points ]




class Hexa():
    """
    Hexa(center)

    methods:- \n
    check_flatness(self)\n
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
        self.triangles = []#list of triangles
        self.obstructs = False
        self.sideLength = 28.868
        self.x = 0 
        self.y = 0
        self.cube=[]
        self.falt_sufrace=[] # may get deprecative
        self.falt_sufrace_points=[]

        for key, value in kwargs.items():
            if key == 'x':
                self.x = value
            elif key == 'y':
                self.y = value
        self.create_hexagon()
        
    
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
                polygons.append(Triangle(Polygon([point_1,point_2,self.center])))
            self.triangles = polygons
        for data in self.points:
            for tri in self.triangles:
                if Point(data.mac_latlon[0],data.mac_latlon[1]).within(tri.sides):
                        tri.points.append(data)
        
        accepted=0
        for tri in self.triangles:
            matrix= []
            for p in tri.points:
                matrix.append([p.pixal_xy[0],p.pixal_xy[1],p.height])
            if len(matrix) > 3:
                tri.flatness = self.isPlaneLine(matrix)
            if tri.flatness >= 1:
                accepted += 1
        
        self.flat = round((accepted/6)*100,2)

        return self.flat
        

    def isPlaneLine(self,XYZ):

        th = 2e-3

        pca = decomposition.PCA()
        pca.fit(XYZ)
        pca_r = pca.explained_variance_ratio_
        t = np.where(pca_r < th)
        return t[0].shape[0]


    def create_cube(self,points , checkNmber = None):
        x,y,z=[],[],[]
        if len(points) < 10 and checkNmber != None:
            #-----not enough points to calaculate
            return
        for data in points:
            x.append(data.pixal_xy[0])
            y.append(data.pixal_xy[1])
            z.append(data.height)
        # if int(max(z)-min(z)) <= 0 and checkNmber!= None:
        #     return 0,0,0,0,0,0,0
        min_total_x , min_total_y , min_total_z = min(x),min(y),int(max(z))
        min_x,min_y,min_z,max_x,max_y,max_z=int(min(x)-min(x)),int(min(y)-min(y)),int(min(z)-min(z)),int(max(x)-min(x)),int(max(y)-min(y)),int(max(z)-min(z))
        cube = np.full((max_z+1, max_x+1,max_y+1 ),-1)
        cube[...]=-1
        for data in points:
            cube[int((data.height)-min(z))][int(data.pixal_xy[0]-min(x))][int(data.pixal_xy[1]-min(y))]=1
        print(cube)
        return cube , min_total_x , min_total_y , min_total_z ,max_x,max_y,max_z

        

    def beta_flatness(self):
        if len(self.points) < 10:
            #-----not enough points to calaculate
            return

        cube , min_total_x , min_total_y , min_total_z ,max_x,max_y,max_z = self.create_cube(self.points,1)

        if type(cube)== type(0) :
            return
        print(len(cube[0]))
        print(len(cube[0][0]))
        scanner =np.full((max_x+1,max_y+1), 9)
        scanner[...]=-1
        for i in range(max_x+1):
            for j in range(max_y+1):
                for z in range(max_z, -1, -1):
                    if cube[z][i][j] >= 1:
                        scanner[i][j] = z

        print(scanner)
        # print(scanner)
        points_accessed = []
        falt_areas = []
        for x in range(len(scanner)):
            for y in range(len(scanner[x])):
                if [x,y] not in points_accessed:
                    flat=[]
                    self.dertmine_surfaces(scanner,points_accessed,flat,x,y,flat)
                    if len(flat) > 1:
                        falt_areas.append(flat)
                        # print(flat)
        flat_surface_points=[]
        for flat in falt_areas:
            flat_points=[]
            for p in flat:
                for poi in self.points:
                    if poi.pixal_xy == [p[0]+min_total_x,p[1]+min_total_y]:
                        flat_points.append(poi)
            flat_surface_points.append(flat_points)
        self.cube = cube
        self.falt_sufrace = falt_areas
        self.falt_sufrace_points = flat_surface_points
        flat_surface_polygons=[]
        #-----------boundries of flat surfaces------------------------------------
        for p in flat_surface_points:
            polygon = []
            polygon2=[]
            cube , min_total_x , min_total_y , min_total_z ,max_x,max_y,max_z = self.create_cube(p)
            # print(cube, min_total_x , min_total_y , min_total_z ,max_x,max_y,max_z)
            scanner =np.full((max_x+1,max_y+1), 9)
            scanner[...]=-1
            for i in range(max_x+1):
                for j in range(max_y+1):
                    for z in range(max_z, -1, -1):
                        if cube[z][i][j] >= 1:
                            scanner[i][j] = z
            # print(scanner)
            for x in range(len(scanner)):
                array = []
                for y in range(len(scanner[x])):
                    if scanner[x][y] != -1:
                        array.append([x,y])
                if len(array) >= 2:
                    for poi in p:
                        if poi.pixal_xy == [array[0][0]+min_total_x,array[0][1]+min_total_y]:
                            polygon.append(poi)
                        if poi.pixal_xy == [array[-1][0]+min_total_x,array[-1][1]+min_total_y]:
                            polygon2.append(poi)
                elif len(array) == 1:
                    for poi in p:
                        if poi.pixal_xy == [array[0][0]+min_total_x,array[0][1]+min_total_y]:
                            polygon.append(poi)
            # print(polygon,'leftside')
            # print(polygon,'rightside')
            if len(polygon) > 2 and len(polygon2) > 0:
                flat_surface_polygons.append(polygon+polygon2[::-1])
                # print(polygon+polygon2[::-1])
                # print("#-----------------00000--------------------")
        self.falt_sufrace_points = flat_surface_polygons

    



    def dertmine_surfaces(self,scanner,points_accessed,falt,x,y,flat):
        checks = 0
        #check left point
        if([x,y] not in points_accessed and scanner[x][y] != -1):
            points_accessed.append([x,y])
            if(x-1 >= 0):
                if  abs(scanner[x][y] - scanner[x-1][y]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,flat,x-1,y,flat)
            else:
                checks+=1
            #check right point
            if(x+1 < len(scanner)):
                if  abs(scanner[x][y] - scanner[x+1][y]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,flat,x+1,y,flat)
            else:
                checks+=1 
            #check bottom point
            if( y+1 < len(scanner[x])):
                if  abs(scanner[x][y] - scanner[x][y+1]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,flat,x,y+1,flat)
            else:
                checks+=1 

            #check top point

            if( y-1 >= 0):
                if  abs(scanner[x][y] - scanner[x][y-1]) <= 1:
                    checks+=1
                    self.dertmine_surfaces(scanner,points_accessed,flat,x,y-1,flat)
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
            print(shapely.geometry.Polygon(square).area)
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
        self.hexas = []
        self.angle = 30
        self.height = 0
    

    def create_fov(self , hexa_center , userPoint):
        height_vector = [abs(hexa_center[0]-userPoint[0]) ,abs(hexa_center[1]-userPoint[1])]
        height_value = math.sqrt(math.pow(hexa_center[0]-userPoint[0],2)+math.pow(hexa_center[1]-userPoint[1],2))
        self.height = height_value 
        hypo = height_value / math.cos((self.angle/2)*(math.pi/180))
        length_new_vector =abs( hypo * math.sin((self.angle/2)*(math.pi/180)))
        height_normal = [height_vector[0]/height_value , height_vector[1]/height_value]
        # diff_x =userPoint[0]-((length_new_vector * hexa_center[1]-userPoint[1]) / height_value)
        # diff_y =userPoint[1]-((length_new_vector * userPoint[0]-hexa_center[0] )/height_value)
        # print(diff_x , diff_y , 'shiiit')
        # diff_x =userPoint[0]+((length_new_vector * hexa_center[1]-userPoint[1]) / height_value)
        # diff_y =userPoint[1]+((length_new_vector * userPoint[0]-hexa_center[0] )/height_value)
        # print(diff_x , diff_y , 'shiiit2')
        cos_90 = 0
        sin_90 = 1
        matrix_height_normal = [[height_normal[0]],[height_normal[1]]]
        matix_clock_wise = [[0 , -1],[1 , 0]]
        matix_anticlock_wise = [[0 , 1],[-1 , 0]]
        vector1 = ((np.matmul(matix_clock_wise,matrix_height_normal)*length_new_vector).ravel()).tolist()
        vector2 = ((np.matmul(matix_anticlock_wise,matrix_height_normal)*length_new_vector).ravel()).tolist()
        vertices = [hexa_center , [userPoint[0]+vector2[0] , userPoint[1]+vector1[1]],[userPoint[0]+vector1[0] , userPoint[1]+vector2[1]]]
        self.view_area = vertices
        self.get_fov_4326()

    def get_fov_4326(self):
        if self.view_area == None :
            return None
        
        transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")
        square_4326 = []
        for p in range(len(self.view_area)):
            x,y = transformer.transform(self.view_area[p][0], self.view_area[p][1])
            square_4326.append([x,y])
        self.view_area = square_4326
        return self.view_area
