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
        data2 , hexas , markerID , buildings = fucade.create_FOV(request,latlon,float(area))
        t2 = time.perf_counter()
        print(f"{t2-t1} , seconds end")
        return JsonResponse({'flatSurfaces':data2 , 'Hexas':hexas , "id":markerID , "buildings":buildings })
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
        data2 , hexas , markerID , buildings = fucade.create_FOV(request,latlon,float(area))
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

