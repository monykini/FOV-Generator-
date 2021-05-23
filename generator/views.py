from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.gis import geos
from . import models

from rest_framework.authtoken.models import Token


from GenClasses.main import FOV_fucade
from .models import modelPoint
from users.models import Profile
from GenClasses.Shapes import userMarker

import jsonpickle
import json
import jsonpickle
import numpy as np
import time


@login_required
def genrator(request,hotspotID=None):
    request.session['key'] = Token.objects.get(user = request.user).key
    request.session['profile'] = Profile.objects.filter(User = request.user).values()[0]
    print(request.session['key'])
    if request.method == 'POST':
        t1 = time.perf_counter()
        latlon = json.loads(request.POST.get('lonlat',[0,0]))
        area = request.POST.get('area',None)
        fucade = FOV_fucade() 
        data2 , hexas , markerID = fucade.create_FOV(request,latlon,float(area))
        t2 = time.perf_counter()
        print(f"{t2-t1} , seconds end")
        return JsonResponse({'flatSurfaces':data2 , 'Hexas':hexas , "id":markerID })
    if hotspotID == None:
        return render(request,'map/map.html')
    else:
        return render(request,'map/map.html',{"hotspotID":hotspotID})


@login_required
def genratorLocation(request,locationID=None):
    request.session['key'] = Token.objects.get(user = request.user).key
    request.session['profile'] = Profile.objects.filter(User = request.user).values()[0]
    print(request.session['key'])
    if request.method == 'POST':
        t1 = time.perf_counter()
        latlon = json.loads(request.POST.get('lonlat',[0,0]))
        area = request.POST.get('area',None)
        fucade = FOV_fucade() 
        data2 , hexas , markerID = fucade.create_FOV(request,latlon,float(area))
        t2 = time.perf_counter()
        print(f"{t2-t1} , seconds end")
        return JsonResponse({'flatSurfaces':data2 , 'Hexas':hexas , "id":markerID })
    if locationID == None:
        return render(request,'map/map.html')
    else:
        return render(request,'map/map.html',{"locationID":locationID})

def get_buildings(request):
    buildings = {"type": "FeatureCollection","features": []}
    for b in models.buildingData.objects.all():
        geojson = json.loads(b.geom.geojson)
        geojson = {'type': 'Feature',"properties":"",'geometry': geojson}
        buildings["features"].append(geojson)

    return JsonResponse(buildings)

def save_Location(request,id):
    if request.method == "POST":
        name = request.POST.get('name',None)
        instance = models.modelUserMarker.objects.get(id=id)
        instance.save_model = True
        instance.name = name
        instance.save()
        return JsonResponse({"status":"ok"})
    return JsonResponse({"status":"not"},status=500)

def model(request):
    # Marker = userMarker([-73.96822854362219,40.76470739485811][::-1],200)
    # print(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
    # wsg48polygon = geos.Polygon(tuple([tuple(i[::-1])  for i in list(Marker.get_square_4326().exterior.coords)]))
    # points = modelPoint.objects.filter(wsg48Point__intersects = wsg48polygon)
    # # { pos: [-1, -1,  1], norm: [ 0,  0,  1], uv: [0, 0], }, 
    # dic = []
    # Xs = []
    # Ys = []
    # Zs = []
    # for p in points:
    #     Xs.append(p.wsg48Point[0])
    #     Ys.append(p.wsg48Point[1])
    #     Zs.append(p.height)

    # minx,maxx = min(Xs),max(Xs)
    # miny,maxy = min(Ys),max(Ys)
    # minz,maxz = min(Zs),max(Zs)

    # cube = create_cube(points)

    # # array = np.array()

    # for x in range(len(cube)):
    #     for y in range(len(cube[x])):
    #         dic.append({"pos":[(points.get(id = cube[x][y]).wsg48Point[0]-minx)*1000, (points.get(id = cube[x][y]).wsg48Point[1]-miny)*1000],(points.get(id = cube[x][y]).height-minz)/10 })

    # for p in points:
    # Geometry.computeVertexNormals()

    # {'points':jsonpickle.encode(dic),'minx':minx,'miny':miny,"minz":minz,"x_len":len(Xs),"y_len":len(Ys)}
    return render(request,'3D/earth.html',)
    
def create_cube(points):
        x,y,z=[],[],[]
        for data in points:
            x.append(json.loads(data.world_pixal_xy)[0])
            y.append(json.loads(data.world_pixal_xy)[1])
            z.append(data.height)
        min_total_x , min_total_y , min_total_z = min(x),min(y),int(max(z))
        min_x,min_y,min_z,max_x,max_y,max_z=int(min(x)-min(x)),int(min(y)-min(y)),int(min(z)-min(z)),int(max(x)-min(x)),int(max(y)-min(y)),int(max(z)-min(z))
        cube = np.full((max_x+1,max_y+1),-1)
        cube[...] = -1
        for data in points:
            cube[int(json.loads(data.world_pixal_xy)[0]-min(x))][int(json.loads(data.world_pixal_xy)[1]-min(y))]=data.id
        return cube
