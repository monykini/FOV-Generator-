from .Shapes import Hexa , Point , userMarker , FOV
from .Grid import hexaGrid
from .Tiles import tileGatherer
from generator import models
from django.contrib.gis import geos
import json
import numpy as np
import random


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
            visibility=0
            for f in fov:
                visibility = f.visibility
                numberOfPoints = models.modelPoint.objects.filter(wsg48Point__intersects = f.wsg48polygon).count()
                fovArea = f.macpolygon.area
                flatSurfaceArea = FS.area
                fovProperties = {'numberOfPoints': numberOfPoints,'fovArea':fovArea,'flatSurfaceArea':flatSurfaceArea , "id":FS.id , "elevation":FS.avgHeight }
                FovGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(f.wsg48polygon.geojson)})
                FovGeojson["properties"] = fovProperties
            
            obsGeojson={"type": "FeatureCollection","features": [],"properties":""}
            obstructions = models.obstructions.objects.filter(flatSurface = FS)
            for obs in obstructions:
                obsGeojson["features"].append({'type': 'Feature',"properties":"",'geometry': json.loads(obs.wsg48Polygon.geojson)})

            obs = json.dumps(obsGeojson)
            properties = json.dumps(FovGeojson)
            geojson = json.loads(FS.wsg48polygon.geojson)
            geojson = {'type': 'Feature','geometry': geojson,"properties":{'fov':properties,'obs':obs,'distance':FS.distance,'height':FS.avgHeight,'visibility':visibility}}
            flatSurfaceGeojson["features"].append(geojson)
        
        hexagons = {"type": "FeatureCollection","features": []}
        
        for hexa in models.modelHexas.objects.filter( wsg48polygon__intersects = marker.wsg48polygon , marker=marker ):
            geojson = json.loads(hexa.wsg48polygon.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson}
            hexagons["features"].append(geojson)

        
        models.modelUserMarker.objects.filter(user= request.user,save_model=False).exclude(id=marker.id).delete()


        
            
        buildings = self.buildingsGeoJson(marker)
        trees = self.treesGeoJson(marker)


        return flatSurfaceGeojson , hexagons , marker.id , buildings , trees


    def view_fov(self,request2,id,*args,**kwargs):
        marker  = models.modelUserMarker.objects.get(id=id)
        # marker.save()
        
        flat_surfaces = models.modelFlatSurface.objects.filter(marker = marker)
        flatSurfaceGeojson={"type": "FeatureCollection","features": []}
        
        for FS in flat_surfaces:
            FovGeojson={"type": "FeatureCollection","features": [],"properties":""}
            fov = models.modelFOV.objects.filter(flatSurface =FS)
            visibility=0
            for f in fov:
                visibility = f.visibility
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
            geojson = {'type': 'Feature','geometry': geojson,"properties":{'fov':properties,'obs':obs,'distance':FS.distance,'height':FS.avgHeight,'visibility':visibility}}
            flatSurfaceGeojson["features"].append(geojson)
        
        hexagons = {"type": "FeatureCollection","features": []}
        
        for hexa in models.modelHexas.objects.filter( wsg48polygon__intersects = marker.wsg48polygon , marker=marker ):
            geojson = json.loads(hexa.wsg48polygon.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson}
            hexagons["features"].append(geojson)

        # models.modelUserMarker.objects.filter(user= request2.user,save_model=False).exclude(id=marker.id).delete()
        buildings = self.buildingsGeoJson(marker)
        trees = self.treesGeoJson(marker)


        return flatSurfaceGeojson , hexagons , marker.id , buildings , trees
    




    def buildingsGeoJson(self,marker):
        hexagons = {"type": "FeatureCollection","features": []}
        for build in models.MLbuildingData.objects.filter(geom__intersects = marker.wsg48polygon , marker=marker ):
            height = random.randint(30,50)
            geojson = json.loads(build.geom.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson,"id":build.id ,"source": "composite", "sourceLayer": "building","state": {"hover": True,"select": True},"tooltip": None,"label": None}
            center = build.geom.centroid
            properties = {
				"extrude": "true",
				"iso_3166_1": "US",
				"underground": "false",
				"height": height,
				"type": "building",
				"min_height": 0,
				"iso_3166_2": "US-NY",
				"uuid": "802C4B41-D2F4-4A51-B2F7-18894CF2C6FE",
				"center": [ center[0], center[1] ],
				"tooltip": "The Louis J. Lefkowitz - State Office Building"
			}

            layer = {"id":"3d-buildings" , "type":"fill-extrusion" ,"source": "composite" ,"source-layer": "buildings" , "minzoom":12,"filter":["==","extrude","true"],"paint":{"fill-extrusion-color":{"r":0.5647058823529412 , "g":0.9333333333333333 , "b":0.5647058823529412 , "a":0.5},"fill-extrusion-height": height,"fill-extrusion-base":0,"fill-extrusion-opacity":0.9}}
                        
            geojson['properties'] = properties
            geojson['layer'] = layer

            hexagons["features"].append(geojson)

        return hexagons



    def treesGeoJson(self,marker):
        hexagons = {"type": "FeatureCollection","features": []}
        for build in models.MLtreesData.objects.filter(geom__intersects = marker.wsg48polygon , marker=marker ):
            height = random.randint(3,4)
            geojson = json.loads(build.geom.geojson)
            geojson = {'type': 'Feature',"properties":"",'geometry': geojson,"id":build.id ,"source": "composite", "sourceLayer": "tree","state": {"hover": True,"select": True},"tooltip": None,"label": None}
            center = build.geom.centroid
            properties = {
				"extrude": "true",
				"iso_3166_1": "US",
				"underground": "false",
				"height": height,
				"type": "building",
				"min_height": 0,
				"iso_3166_2": "US-NY",
				"uuid": "802C4B41-D2F4-4A51-B2F7-18894CF2C6FE",
				"center": [ center[0], center[1] ],
				"tooltip": "The Louis J. Lefkowitz - State Office Building"
			}

            layer = {"id":"3d-trees" , "type":"fill-extrusion" ,"source": "composite" ,"source-layer": "trees" , "minzoom":12,"filter":["==","extrude","true"],"paint":{"fill-extrusion-color":{"r":0.5647058823529412 , "g":0.9333333333333333 , "b":0.5647058823529412 , "a":0.5},"fill-extrusion-height": height,"fill-extrusion-base":0,"fill-extrusion-opacity":0.9}}
                        
            geojson['properties'] = properties
            geojson['layer'] = layer

            hexagons["features"].append(geojson)

        return hexagons