from .Shapes import Hexa , Point , userMarker , FOV
from .Grid import hexaGrid
from .Tiles import tileGatherer
from generator import models
from django.contrib.gis import geos
import json
import numpy as np


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
        marker.save()
        
        Marker.id = marker.id
        Grid = hexaGrid(Marker)
        
        Tiler = tileGatherer(np.asarray(Marker.get_square_4326().exterior.coords),markerID = marker.id,markerObject = marker)
        Tiler.convert_raster_tiles()
        
        Grid.Mapper()
        
        flat_surfaces = models.modelFlatSurface.objects.filter(marker = marker)
        flatSurfaceGeojson={"type": "FeatureCollection","features": []}
        
        for FS in flat_surfaces:
            FovGeojson={"type": "FeatureCollection","features": [],"properties":""}
            fov = models.modelFOV.objects.filter(flatSurface =FS)
            for f in fov:
                numberOfPoints = models.modelPoint.objects.filter(wsg48Point__intersects = f.wsg48polygon).count()
                fovArea = f.macpolygon.area
                flatSurfaceArea = FS.area
                fovProperties = {'numberOfPoints': numberOfPoints,'fovArea':fovArea,'flatSurfaceArea':flatSurfaceArea , "id":FS.id , "elevation":FS.avgHeight}
                FovGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(f.wsg48polygon.geojson)})
                FovGeojson["properties"] = fovProperties
            
            obsGeojson={"type": "FeatureCollection","features": [],"properties":""}
            obstructions = models.obstructions.objects.filter(flatSurface = FS)
            for obs in obstructions:
                obsGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(obs.wsg48Polygon.geojson)})

            obs = json.dumps(obsGeojson)
            properties = json.dumps(FovGeojson)
            geojson = json.loads(FS.wsg48polygon.geojson)
            geojson = {'type': 'Feature','geometry': geojson,"properties":{'fov':properties,'obs':obs,'distance':FS.distance,'height':FS.avgHeight}}
            flatSurfaceGeojson["features"].append(geojson)
        
        hexagons = {"type": "FeatureCollection","features": []}
        
        for hexa in models.modelHexas.objects.filter( wsg48polygon__intersects = marker.wsg48polygon , marker=marker ):
            geojson = json.loads(hexa.wsg48polygon.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson}
            hexagons["features"].append(geojson)

        models.modelUserMarker.objects.filter(user= request.user,save_model=False).exclude(id=marker.id).delete()


        
            


        return flatSurfaceGeojson , hexagons , marker.id


    def view_fov(request,request2,id,*args,**kwargs):
        print(request2,'lol')
        marker  = models.modelUserMarker.objects.get(id=id)
        # marker.save()
        
        flat_surfaces = models.modelFlatSurface.objects.filter(marker = marker)
        flatSurfaceGeojson={"type": "FeatureCollection","features": []}
        
        for FS in flat_surfaces:
            FovGeojson={"type": "FeatureCollection","features": [],"properties":""}
            fov = models.modelFOV.objects.filter(flatSurface =FS)
            for f in fov:
                numberOfPoints = models.modelPoint.objects.filter(wsg48Point__intersects = f.wsg48polygon).count()
                fovArea = f.macpolygon.area
                flatSurfaceArea = FS.area
                fovProperties = {'numberOfPoints': numberOfPoints,'fovArea':fovArea,'flatSurfaceArea':flatSurfaceArea , "id":FS.id , "elevation":FS.avgHeight}
                FovGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(f.wsg48polygon.geojson)})
                FovGeojson["properties"] = fovProperties
            
            obsGeojson={"type": "FeatureCollection","features": [],"properties":""}
            obstructions = models.obstructions.objects.filter(flatSurface = FS)
            for obs in obstructions:
                obsGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(obs.wsg48Polygon.geojson)})

            obs = json.dumps(obsGeojson)
            properties = json.dumps(FovGeojson)
            geojson = json.loads(FS.wsg48polygon.geojson)
            geojson = {'type': 'Feature','geometry': geojson,"properties":{'fov':properties,'obs':obs,'distance':FS.distance,'height':FS.avgHeight}}
            flatSurfaceGeojson["features"].append(geojson)
        
        hexagons = {"type": "FeatureCollection","features": []}
        
        for hexa in models.modelHexas.objects.filter( wsg48polygon__intersects = marker.wsg48polygon , marker=marker ):
            geojson = json.loads(hexa.wsg48polygon.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson}
            hexagons["features"].append(geojson)

        # models.modelUserMarker.objects.filter(user= request2.user,save_model=False).exclude(id=marker.id).delete()

        return flatSurfaceGeojson , hexagons , marker.id
    


    def get_ti(self,latlon):
        Marker = userMarker(latlon,200)
        Marker.get_square()
        area_array = tileGatherer(Marker)
        area_array.conver_raster_tiles()
        return area_array.areaArray


    def test_fov(self):
        fov = FOV()
        fov.create_fov([0,10],[10,0])
