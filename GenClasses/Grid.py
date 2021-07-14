import math
import json
from shapely.geometry import Point, Polygon, LineString
from pyproj import Transformer
from .Shapes import Hexa , Points , userMarker , flatSurface , FOV 
from generator.models import modelHexas,modelUserMarker,modelPoint,modelFOV,modelFlatSurface,buildingData,obstructions
from django.contrib.gis import geos
from django.core.exceptions import ObjectDoesNotExist
from .Exceptions import WaterTile ,NoDataAvailable
from .Tiles import latlon_to_pixal_Converter
from subprocess import Popen, PIPE
from osgeo import gdal,ogr,osr
import rasterio
import rasterio.features
from rasterio.features import sieve
import os
import pandas as pd
from multiprocessing import Pool
import threading
import traceback
import numpy as np
import shapely

class hexaGrid():
        """
        creates a hexagrid \n
        hexaGrid(userMarker)
        methods: \n
        calculate_grid(self) :- creates a hexagrid
        Mapper(self,tilesArray) :- takes tilesArray form tile_gather class and maps each point to respective hexa in grid
        """
        def __init__(self,userMarker):
                self.hexas = []
                self.userMarker = userMarker
                self.sideLength = 28.868
                self.flat_surfaces = []
                self.CoverageArea = 405.95
                self.converter = latlon_to_pixal_Converter()
                self.calculate_grid()

        def calculate_grid(self):
                """
                returns an array of Points describing hexagons centers that are inside the given bounding_box \n
                :return: The hexagon grid \n
                """
                grid = []

                v_step = math.sqrt(3) * self.sideLength
                h_step = 1.5 * self.sideLength


                bbox = list(self.userMarker.get_square().exterior.coords)

                x_min = bbox[3][0]
                x_max = bbox[1][0]
                y_min = bbox[1][1]
                y_max = bbox[3][1]


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
                                hexa = Hexa([c_x, c_y],x=x,y=y)
                                macpoint = geos.Point(c_y, c_x)
                                wsg48point = geos.Point(c_y1, c_x1)
                                wsg48Polygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(hexa.get_sides_4326().exterior.coords)]))
                                macpolygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(hexa.create_hexagon().exterior.coords)]))
                                modelhex = modelHexas(marker = modelUserMarker.objects.get(id=self.userMarker.id) ,wsg48polygon = wsg48Polygon , macpolygon= macpolygon , maccenter=macpoint , wsg48center = wsg48point)
                                modelhex.save()
                                hexa.id = modelhex.id
                                grid.append(hexa)
                                c_y += v_step
                                y+=1
                        c_x += h_step
                        c_y = v_start_array[v_start_idx]
                        v_start_idx = (v_start_idx + 1) % 2
                        x+=1
                self.hexas = grid
                return grid


        

        def Mapper(self):
                temp=[]
                for hexa in self.hexas:
                        hexi = modelHexas.objects.get(id = hexa.id)
                        buildings = buildingData.objects.filter(geom__intersects = hexi.wsg48polygon)
                        points = modelPoint.objects.filter(wsg48Point__intersects=hexi.wsg48polygon)
                        lytes = {}
                        for b in buildings:
                                p = points.filter(wsg48Point__intersects = b.geom)
                                for pi in p:
                                        lytes[pi.id] = b.height
                        for point in points:
                                data = Points(list(point.wsg48Point.coords)[::-1], list(point.macPoint.coords)[::-1] , json.loads(point.pixal_xy) , json.loads(point.world_pixal_xy) , point.height+lytes.get(point.id,0) , json.loads(point.color))
                                hexa.points.append(data)

                        hexa.beta_flatness()

                self.assign_falt_surfaces()
                return temp

        def assign_falt_surfaces(self):
                self.create_raster_beta()


                transformer_4326 = Transformer.from_crs("epsg:3857", "epsg:4326")
                transformer_mac = Transformer.from_crs("epsg:4326","epsg:3857")
                
                marker = modelUserMarker.objects.get(id=self.userMarker.id)
                markerx,markery = self.converter.LatLongToPixelXYOSM(self.userMarker.latlon[0],self.userMarker.latlon[1],15)
                
                markerBuilding = 0
                try:
                        markerPoint = modelPoint.objects.get(world_pixal_xy = json.dumps([markerx,markery]))
                except ObjectDoesNotExist:
                        raise NoDataAvailable
                
                if buildingData.objects.filter(geom__intersects = markerPoint.wsg48Point).exists():
                        markerBuilding =  buildingData.objects.filter(geom__intersects = markerPoint.wsg48Point)[0].height

                self.userMarker.Height = markerPoint.height + markerBuilding

                total_hexas = len(self.hexas)
                print(total_hexas)
                total_threads = 8
                division = math.ceil(total_hexas/total_threads)
                pools=[]

                for p in range(total_threads):
                        pools.append(threading.Thread(target = self.flat_pool_proces, args=(p*division,(p+1)*division,transformer_4326,transformer_mac,marker)))
                        pools[p].start()
                        

                for p in range(total_threads):
                        pools[p].join()
                        print('ok')


                # for hexa in self.hexas:
                #         i=0 
                #         for flatpoints in hexa.falt_sufrace_points:
                #                 flat_Surface = flatSurface(flatpoints,hexa)
                #                 flat_Surface.insidePoints = hexa.falt_sufrace_allPoints[i]
                #                 flat_Surface.get_area_flat_surface()
                #                 # print("area" ,flat_Surface.area )
                #                 if flat_Surface.area >= self.CoverageArea:
                #                         fov  = FOV()
                #                         fov.create_fov(flat_Surface.center  , self.userMarker.get_latlonMac())
                #                         if (fov.height >= 100 and fov.height <=4000) :
                #                                 # fov.get_obstruction(flat_Surface.insidePoints,flat_Surface.modeHeight,self.userMarker)
                #                                 flat_Surface.fov = fov
                #                                 # print(flat_Surface.get_sides_4326())
                #                                 wsg48polygon = Polygon(tuple([tuple(li[::-1]) for li in flat_Surface.get_sides_4326()]))
                #                                 macpolygon = Polygon(tuple([tuple(li[::-1]) for li in flat_Surface.get_sides_mac()]))
                #                                 distance = Point(flat_Surface.center[0],flat_Surface.center[1]).distance(Point(marker.macpoint[1],marker.macpoint[0]))
                #                                 FS = modelFlatSurface(marker = marker ,wsg48polygon =geos.Polygon(tuple(wsg48polygon.exterior.coords)) ,macpolygon= geos.Polygon(tuple(macpolygon.exterior.coords)) , avgHeight = flat_Surface.modeHeight,area = flat_Surface.area,center = geos.Point(tuple(flat_Surface.center_wsg)[::-1]),distance=distance)
                #                                 FS.save()
                #                                 wsg48polygon = Polygon(tuple([tuple(li[::-1]) for li in fov.get_fov_4326()]))
                #                                 macpolygon = Polygon(tuple([tuple(li[::-1]) for li in fov.view_area]))
                #                                 F_O_V = modelFOV(flatSurface=FS,wsg48polygon=geos.Polygon(tuple(wsg48polygon.exterior.coords)),macpolygon=geos.Polygon(tuple(macpolygon.exterior.coords)),height=fov.height,sign=fov.sign)
                #                                 F_O_V.save()
                #                                 # get_obstruction(F_O_V,self.userMarker,FS,self.converter,transformer_mac,transformer_4326)
                #                                 self.flat_surfaces.append(flat_Surface)
                #                 i+=1
                self.get_obstructions()
                return self.flat_surfaces
        
        
        def flat_pool_proces(self,start,end,transformer_4326,transformer_mac,marker):
                # transformer_4326 = Transformer.from_crs("epsg:3857", "epsg:4326")
                # transformer_mac = Transformer.from_crs("epsg:4326","epsg:3857")
                try:
                        for hexa in self.hexas[start:end]:
                                i=0 
                                for flatpoints in hexa.falt_sufrace_points:
                                        flat_Surface = flatSurface(flatpoints,hexa)
                                        flat_Surface.insidePoints = hexa.falt_sufrace_allPoints[i]
                                        flat_Surface.get_area_flat_surface(transformer_4326)
                                        # print("area" ,flat_Surface.area )
                                        if flat_Surface.area >= self.CoverageArea:
                                                fovs = []
                                                j=0
                                                for endpoint in flat_Surface.get_sides_mac():
                                                        fovs.append(FOV())
                                                        fovs[j].create_fov(endpoint  , self.userMarker.get_latlonMac(tranformer = transformer_mac))
                                                        j+=1
                                                fov  = FOV()
                                                fov.center = True
                                                fov.create_fov(flat_Surface.center  , self.userMarker.get_latlonMac(tranformer = transformer_mac))
                                                fovs.append(fov)
                                                print(len(fovs),"fovs created")
                                                if (fov.height >= 100 and fov.height <=4000) :
                                                        # fov.get_obstruction(flat_Surface.insidePoints,flat_Surface.modeHeight,self.userMarker)
                                                        flat_Surface.fov = fov
                                                        # print(flat_Surface.get_sides_4326())
                                                        wsg48polygon = Polygon(tuple([tuple(li[::-1]) for li in flat_Surface.get_sides_4326()]))
                                                        macpolygon = Polygon(tuple([tuple(li[::-1]) for li in flat_Surface.get_sides_mac()]))
                                                        distance = Point(flat_Surface.center[0],flat_Surface.center[1]).distance(Point(marker.macpoint[1],marker.macpoint[0]))
                                                        FS = modelFlatSurface(marker = marker ,wsg48polygon =geos.Polygon(tuple(wsg48polygon.exterior.coords)) ,macpolygon= geos.Polygon(tuple(macpolygon.exterior.coords)) , avgHeight = flat_Surface.modeHeight,area = flat_Surface.area,center = geos.Point(tuple(flat_Surface.center_wsg)[::-1]),distance=distance)
                                                        FS.save()
                                                        for fov in fovs:
                                                                wsg48polygon = Polygon(tuple([tuple(li[::-1]) for li in fov.get_fov_4326(transformer_4326)]))
                                                                macpolygon = Polygon(tuple([tuple(li[::-1]) for li in fov.view_area]))
                                                                # startx,starty = transformer_4326.transform(fov.start[0],fov.start[1])
                                                                F_O_V = modelFOV(flatSurface=FS,wsg48polygon=geos.Polygon(tuple(wsg48polygon.exterior.coords)),macpolygon=geos.Polygon(tuple(macpolygon.exterior.coords)),height=fov.height,sign=fov.sign,start = geos.Point(fov.start[0],fov.start[1]),center = fov.center)
                                                                F_O_V.save()
                                                        # get_obstruction(F_O_V,self.userMarker,FS,self.converter,transformer_mac,transformer_4326)
                                                        # self.flat_surfaces.append(flat_Surface)
                                        i+=1
                except Exception as e:
                        print(traceback.print_exc())


        def convert_pixal(self,poly,points):
                po = []
                for p in poly.coords[0]:
                        x,y = int(p[0]+0.5) , int(p[1]-0.5)
                        poi = points.get(world_pixal_xy = json.dumps([x,y])) 
                        po.append((poi.wsg48Point[0],poi.wsg48Point[1]))
                po = tuple(po)
                poly = geos.Polygon(po)
                return poly

        def convert_mac_lat(self,poly,transformer_4326):
                po = []
                for p in poly.coords[0]:
                        x,y = transformer_4326.transform(p[0],p[1])
                        po.append((y,x))
                po = tuple(po)
                poly = geos.Polygon(po)
                return poly

        def create_raster_beta(self):
                workingDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

                marker = modelUserMarker.objects.get(id=self.userMarker.id)

                userRasterPath = f"userRasters/{marker.user.username}/"


                points = modelPoint.objects.filter(wsg48Point__intersects =marker.wsg48polygon)
                buildings = buildingData.objects.filter(geom__intersects=marker.wsg48polygon)
                dict_points=[]
                for p in points:
                        x = p.macPoint[1]
                        y = p.macPoint[0]
                        height = p.height
                        b = buildings.filter(geom__intersects=p.wsg48Point)
                        if len(b) > 0:
                                height = height + b[0].height
                        temp = {"x":x,"y":y,"height":height*10}
                        dict_points.append(temp)
                df= pd.DataFrame(dict_points)
                # print(df)
                df = df.sort_values(["x","y"],ascending=[True,True])
                df.to_csv(userRasterPath+f'uneven_{marker.id}.csv',index=False,header=False,sep=" ")
                print(df)
                # dict_points = []

                x = points.first().wsg48Point[1]

                req_interval = 2.388657134

                # if (x > -40 and x <= -20 ) or (x >= 20 and x < 40):
                #         req_interval = 2.245
                # elif (x > -60 and x <= -40 ) or (x >= 40 and x < 60):
                #         req_interval = 2.388657134
                # elif (x > -80 and x <= -60 ) or (x >= 60 and x < 80):
                #         req_interval = 1.194
                # elif x <= -80 or x >= 80:
                #         req_interval = 0.415

                print(req_interval)
                ys=[]
                df = df.sort_values(["y","x"],ascending=[True,True])
                df.reset_index(inplace = True, drop = True)
                previous_y = 0
                og_prev_y = 0
                for ID , row in df.iterrows():
                        if ID == 0 :
                                previous_y = row["y"]
                                og_prev_y = row["y"]
                                y = row["y"]
                        else:
                                if og_prev_y == row['y']:
                                        y = previous_y
                                else:    
                                        # difference_y = abs(abs(previous_y) - abs(row["y"]))
                                        # gap = difference_y - req_interval
                                        y = previous_y + req_interval
                                previous_y = y
                                og_prev_y = row["y"]
                                # lol
                        ys.append(y)
                # print(ys)
                xs=[]
                df = df.sort_values(["x","y"],ascending=[True,True])
                df.reset_index(inplace = True, drop = True)
                previous_x = 0
                og_prev_x = 0
                for ID , row in df.iterrows():
                        if ID == 0 :
                                previous_x = row["x"]
                                og_prev_x = row["x"]
                                x = row["x"]
                        else:
                                if og_prev_x == row['x']:
                                        x = previous_x
                                else:    
                                        # difference_x = abs(abs(previous_x) - abs(row["x"]))
                                        # gap = difference_x - req_interval
                                        x = previous_x + req_interval
                                previous_x = x
                                og_prev_x = row["x"]
                                # lol
                        xs.append(x)

                df = df.sort_values(["x","y"],ascending=[True,True])
                df['x'] = xs
                df = df.sort_values(["y","x"],ascending=[True,True])
                df['y'] = ys
                
                
                df = df.sort_values(["x","y"],ascending=[True,False])
                
                
                df.to_csv(userRasterPath+f'uneven_{marker.id}.xyz',index=False,header=False,sep=" ")

                if os.path.exists(userRasterPath+f"uneven_{marker.id}.vrt"):
                        os.remove(userRasterPath+f'uneven_{marker.id}.vrt')
        

                dem = gdal.Translate(userRasterPath+f"unevenInt_{marker.id}.tif",userRasterPath+f'uneven_{marker.id}.xyz',outputSRS = "EPSG:3857")
                dem = None




        def get_obstructions(self):
                marker = modelUserMarker.objects.get(id=self.userMarker.id)
                path = f"userRasters/{marker.user.username}/"
                transformer_4326 = Transformer.from_crs("epsg:3857", "epsg:4326")
                transformer_mac = Transformer.from_crs("epsg:4326","epsg:3857")

                flatSurfaces = list(modelFlatSurface.objects.filter(marker = marker))
                total_flatSurfaces = len(flatSurfaces)
                print(total_flatSurfaces)
                total_threads = 8
                division = math.ceil(total_flatSurfaces/total_threads)
                pools=[]
                obs = []

                for p in range(total_threads):
                        pools.append(threading.Thread(target = self.get_obstruction_process, args=(p*division,(p+1)*division,marker,path,transformer_4326,transformer_mac,obs,flatSurfaces)))
                        pools[p].start()
                        

                for p in range(total_threads):
                        pools[p].join()
                        print('ok')

                obs = []
                for fs in modelFlatSurface.objects.filter(marker = marker):
                        if len(fs.obstructions_set.all()) == 0:
                                obs.append(fs.id)
                modelFlatSurface.objects.filter(id__in = obs).delete()
                modelFOV.objects.filter(center=False).delete()


        def get_obstruction_process(self,start,end,marker,path,transformer_4326,transformer_mac,obs,flatSurfaces):
                for fs in flatSurfaces[start:end]:
                        inputfile = path+f"unevenInt_{marker.id}.tif"
                        fovs = []
                        polys = []
                        print(len(modelFOV.objects.filter(flatSurface = fs)),"fovs saved")
                        for fov in modelFOV.objects.filter(flatSurface = fs):
                                outputfile = path+ f'cliped-{marker.id}_viewshed_{fs.id}_{fov.id}.tif'
                                workingDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                # x,y = transformer_mac.transform(fs.center[1],fs.center[0])
                                x,y = fov.start[0],fov.start[1]
                                print(x,y)
                                
                                process = Popen(['gdal_viewshed','-b','1','-md','0','-ox',f'{x}','-oy',f'{y}','-oz','5',inputfile,outputfile], stdout=PIPE, stderr=PIPE,cwd=workingDir)
                                stdout, stderr = process.communicate()
                                print(stdout, stderr)

                                shapes = []
                                try:
                                        with rasterio.open(outputfile) as src:
                                                crs = src.crs
                                                src_band = src.read(1)
                                                sieved = sieve(src_band, 5, out=np.zeros(src.shape, src.dtypes[0]),connectivity = 8)
                                                unique_values = [255]
                                                shapes = list(rasterio.features.shapes(sieved, transform=src.transform))
                                except Exception as e:
                                        # obs.append(fs.id)
                                        continue
                                # print(shapes)
                                # lol
                                # fov = modelFOV.objects.get(flatSurface = fs)
                                for s in shapes:
                                        if s[1] >= 250:
                                                poly = geos.Polygon(tuple(s[0]['coordinates'][0]))
                                                poly = self.convert_mac_lat(poly,transformer_4326)
                                                poly = Polygon(poly.coords[0])
                                                polys.append(poly)
                        
                        fov = modelFOV.objects.filter(flatSurface = fs , center = True).first()
                        area = 0
                        if len(polys) > 2:
                                polys2 = []
                                for p in polys:
                                        polys2.append(p.buffer(0))
                                shapes = shapely.ops.unary_union(polys2)   
                                
                                if shapes.geom_type == 'Polygon':
                                        poly = tuple(shapes.exterior.coords)
                                        poly = geos.Polygon(poly)
                                        if poly.intersects(marker.wsg48point):
                                                clipped = fov.wsg48polygon.intersection(poly)
                                                area += clipped.area
                                                if clipped.geom_typeid == 3:
                                                        obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = clipped)
                                                if clipped.geom_typeid == 4:
                                                        for poly in clipped.coords:
                                                                poly = geos.Polygon(poly)
                                                                obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = poly)
                                else:
                                        for s in shapes:
                                                # if s[1] >= 250: #changes to >=
                                                poly = tuple(s.exterior.coords)
                                                poly = geos.Polygon(poly)
                                                if poly.intersects(marker.wsg48point):
                                                        clipped = fov.wsg48polygon.intersection(poly)
                                                        area += clipped.area
                                                        if clipped.geom_typeid == 3:
                                                                obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = clipped)
                                                        if clipped.geom_typeid == 4:
                                                                for poly in clipped.coords:
                                                                        poly = geos.Polygon(poly)
                                                                        obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = poly)

                                                # obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = poly )
                        elif len(polys) == 1:
                                poly = geos.Polygon(tuple(polys[0].exterior.coords))
                                if poly.intersects(marker.wsg48point):
                                        clipped = fov.wsg48polygon.intersection(poly)
                                        area += clipped.area
                                        if clipped.geom_typeid == 3:
                                                obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = clipped)
                                        if clipped.geom_typeid == 4:
                                                for poly in clipped.coords:
                                                        poly = geos.Polygon(poly)
                                                        obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = poly)
                                # obstructions.objects.create(flatSurface  = fs ,wsg48Polygon = poly )

                        visibility = area/fov.wsg48polygon.area
                        fov.visibility = visibility
                        fov.save()
                        modelFOV.objects.filter(id__in=fovs).delete()