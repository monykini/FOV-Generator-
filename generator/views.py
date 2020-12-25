from django.shortcuts import render
from django.http import JsonResponse
from GenClasses.main import FOV_fucade

def genrator(request):
    if request.method == 'POST':
        print(request.method)
        lat = request.POST.get('lati',None)
        lon = request.POST.get('loni',None)
        print(lat,lon)
        fucade = FOV_fucade() 
        view , square = fucade.create_FOV([lat,lon])
        data={'type': 'FeatureCollection','features': [],}
        all_hexagons = []
        for v in view:
            hexagon = {'type': 'Feature',"properties":"",'geometry': {'type': 'Polygon','coordinates': []}}
            hexagon['geometry']['coordinates'].append([li[::-1] for li in v.get_sides_4326()])
            hexagon["properties"]={"avgheight":v.get_avgHeight(),"flatness":v.check_flatness() , "points":len(v.points)}
            triangle=[]
            for t in v.triangles:
                tri={"sides":t.flatness}
                poin = []
                for p in t.points:
                    poin.append(p.height)
                if len(poin) > 1:
                    tri['pointsMax'] = max(poin)
                    tri['pointsMin'] = min(poin)
                triangle.append(tri)
            hexagon["properties"]['triangles']=triangle
            all_hexagons.append(hexagon)
        data['features']= all_hexagons

        data2={'type': 'FeatureCollection','features': [],}
        square2 = {'type': 'Feature',"properties":"",'geometry': {'type': 'Polygon','coordinates': []}}
        square2['geometry']['coordinates'].append([li[::-1] for li in square])
        data2['features']= [square2]
        return JsonResponse({'data':data , 'square':data2})
    return render(request,'map/map.html')
