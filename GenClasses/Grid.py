import math
import json
from shapely.geometry import Point, Polygon, LineString
from pyproj import Transformer
from .Shapes import Hexa , Points , userMarker , flatSurface , FOV , get_obstruction
from generator.models import modelHexas,modelUserMarker,modelPoint,modelFOV,modelFlatSurface,buildingData
from django.contrib.gis import geos
from django.core.exceptions import ObjectDoesNotExist
from .Exceptions import WaterTile ,NoDataAvailable
from .Tiles import latlon_to_pixal_Converter

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

                for hexa in self.hexas:
                        i=0 
                        for flatpoints in hexa.falt_sufrace_points:
                                flat_Surface = flatSurface(flatpoints,hexa)
                                flat_Surface.insidePoints = hexa.falt_sufrace_allPoints[i]
                                flat_Surface.get_area_flat_surface()
                                if flat_Surface.area >= self.CoverageArea:
                                        fov  = FOV()
                                        fov.create_fov(flat_Surface.center  , self.userMarker.get_latlonMac())
                                        if (fov.height >= 100 and fov.height <=4000) and (flat_Surface.modeHeight >= self.userMarker.Height) :
                                                # fov.get_obstruction(flat_Surface.insidePoints,flat_Surface.modeHeight,self.userMarker)
                                                flat_Surface.fov = fov
                                                wsg48polygon = Polygon(tuple([tuple(li[::-1]) for li in flat_Surface.get_sides_4326()]))
                                                macpolygon = Polygon(tuple([tuple(li[::-1]) for li in flat_Surface.get_sides_mac()]))
                                                distance = Point(flat_Surface.center[0],flat_Surface.center[1]).distance(Point(marker.macpoint[1],marker.macpoint[0]))
                                                FS = modelFlatSurface(marker = marker ,wsg48polygon =geos.Polygon(tuple(wsg48polygon.exterior.coords)) ,macpolygon= geos.Polygon(tuple(macpolygon.exterior.coords)) , avgHeight = flat_Surface.modeHeight,area = flat_Surface.area,center = geos.Point(tuple(flat_Surface.center_wsg)[::-1]),distance=distance)
                                                FS.save()
                                                wsg48polygon = Polygon(tuple([tuple(li[::-1]) for li in fov.get_fov_4326()]))
                                                macpolygon = Polygon(tuple([tuple(li[::-1]) for li in fov.view_area]))
                                                F_O_V = modelFOV(flatSurface=FS,wsg48polygon=geos.Polygon(tuple(wsg48polygon.exterior.coords)),macpolygon=geos.Polygon(tuple(macpolygon.exterior.coords)),height=fov.height,sign=fov.sign)
                                                F_O_V.save()
                                                get_obstruction(F_O_V,self.userMarker,FS,self.converter,transformer_mac,transformer_4326)
                                                self.flat_surfaces.append(flat_Surface)
                                i+=1
                return self.flat_surfaces