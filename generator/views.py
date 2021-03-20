from django.shortcuts import render
from django.http import JsonResponse
from GenClasses.main import FOV_fucade
import jsonpickle
import json


def genrator(request):
    if request.method == 'POST':
        latlon = json.loads(request.POST.get('lonlat',[0,0]))
        area = request.POST.get('area',None)
        fucade = FOV_fucade() 
        data2 , hexas = fucade.create_FOV(request,latlon,float(area))
        return JsonResponse({'flatSurfaces':data2 , 'Hexas':hexas })
    return render(request,'map/map.html')





