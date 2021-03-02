from django.shortcuts import render
from django.http import JsonResponse
from GenClasses.main import FOV_fucade
from scripts.jsonToFiles import jsonToFiles 
import jsonpickle
import json


def genrator(request):
    if request.method == 'POST':
        latlon = json.loads(request.POST.get('lonlat',[0,0]))
        area = request.POST.get('area',None)
        fucade = FOV_fucade() 
        hexas , square, points_tile , flat_surfaces = fucade.create_FOV(latlon,float(area))

        data2={'type': 'FeatureCollection','features': [],}
        allsquare=[]

        for v in flat_surfaces:
            f_o_v = [ f[::-1]  for f in v.fov.view_area]
            square2 = {'type': 'Feature',"properties":"",'geometry': {'type': 'Polygon','coordinates': []}}
            f_o_v = {'type': 'FeatureCollection','features': [{'type': 'Feature',"properties":"",'geometry': {'type': 'Polygon','coordinates': [f_o_v]}}],}
            square2["properties"]={'area':v.area, 'points':len(v.points) , 'fovArea' : v.fov.area ,'fov':f_o_v}
            square2['geometry']['coordinates'].append([li[::-1] for li in v.get_sides_4326()])
            allsquare.append(square2)
        data2['features']= allsquare

        return JsonResponse({'flatSurfaces':data2 })

    return render(request,'map/map.html')

def processData(request):
    jsonToFiles('newyork','newyork.geojson')
    return JsonResponse({'status':'ok'})
