from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.gis import geos

from GenClasses.main import FOV_fucade
from .models import modelPoint
from GenClasses.Shapes import userMarker

import jsonpickle
import json
import jsonpickle
from numba import jit , njit
from numba.types import float64,int32,int64,float32,List
import numpy as np
import time


@login_required
def genrator(request):
    if request.method == 'POST':
        t1 = time.perf_counter()
        latlon = json.loads(request.POST.get('lonlat',[0,0]))
        area = request.POST.get('area',None)
        fucade = FOV_fucade() 
        data2 , hexas = fucade.create_FOV(request,latlon,float(area))
        t2 = time.perf_counter()
        print(f"{t2-t1} , seconds end")
        return JsonResponse({'flatSurfaces':data2 , 'Hexas':hexas })
    return render(request,'map/map.html')


def model(request):
    Marker = userMarker([-73.96822854362219,40.76470739485811][::-1],100)
    print(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
    wsg48polygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
    points = modelPoint.objects.filter(wsg48Point__intersects = wsg48polygon)
    geoJsonPoints={"type": "FeatureCollection","features": []}
    Xs=[]
    Ys=[]
    dic = {}
    for p in points:
        pixal_xy = json.loads(p.world_pixal_xy)
        # geoJsonPoints["features"].append({"type": "Feature","properties":{"pixal":pixal_xy,"height":p.height},"geometry": json.loads(p.wsg48Point.geojson)})
        dic[str(pixal_xy)] = p.height
        if pixal_xy[0] not in Xs:
            Xs.append(pixal_xy[0])
        if pixal_xy[1] not in Ys:
            Ys.append(pixal_xy[1])
    minx = min(Xs)
    miny = min(Ys)
    matrix={}
    for x in Xs:
        for y in Ys:
            matrix[f'{x-minx},{y-miny}']= dic[str([x,y])]
    print(minx)
    print(miny)
    print(matrix)
    
    return render(request,'3D/earth.html',{'points':jsonpickle.encode(matrix),'minx':minx,'miny':miny})
    
