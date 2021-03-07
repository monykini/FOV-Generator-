from .Shapes import Hexa , Point , userMarker , FOV
from .Grid import hexaGrid
from .Tiles import tileGatherer
from generator import models
from django.contrib.gis import geos
import json


class FOV_fucade():
    """
    docstring
    """
    
    def create_FOV(self,request,latlon,size):
        user = request.user
        Marker = userMarker(latlon,size)
        wsg48polygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
        macpolygon = geos.Polygon(tuple(Marker.get_square().exterior.coords)[:][::-1])
        wsg48point = geos.Point(Marker.latlon[1],Marker.latlon[0])
        macpoint = Marker.get_latlonMac()
        macpoint = geos.Point(macpoint[1],macpoint[0])
        marker  = models.modelUserMarker(user = user , wsg48point =wsg48point ,wsg48polygon =wsg48polygon ,macpoint=macpoint , macpolygon=macpolygon)
        print(marker.wsg48polygon.geojson)
        marker.save()
        Marker.id = marker.id
        Grid = hexaGrid(Marker)
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        Grid.Mapper()
        flat_surfaces = models.modelFlatSurface.objects.filter(marker = marker)
        flatSurfaceGeojson={"type": "FeatureCollection","features": []}
        for FS in flat_surfaces:
            FovGeojson={"type": "FeatureCollection","features": [],"properties":""}
            fov = models.modelFOV.objects.filter(flatSurface =FS)
            for f in fov:
                FovGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(f.wsg48polygon.geojson)})
                print(FovGeojson["features"])
            properties = json.dumps(FovGeojson)
            geojson = json.loads(FS.wsg48polygon.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson,"properties":{'fov':properties}}
            flatSurfaceGeojson["features"].append(geojson)
        return flatSurfaceGeojson


    def get_ti(self,latlon):
        Marker = userMarker(latlon,200)
        Marker.get_square()
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        return area_array.areaArray


    def test_fov(self):
        fov = FOV()
        fov.create_fov([0,10],[10,0])
        print(fov.view_area)
