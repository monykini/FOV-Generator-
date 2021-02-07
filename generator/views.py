from django.shortcuts import render
from django.http import JsonResponse
from GenClasses.main import FOV_fucade
import jsonpickle
def genrator(request):
    if request.method == 'POST':
        lat = request.POST.get('lati',None)
        lon = request.POST.get('loni',None)
        fucade = FOV_fucade() 
        view , square,points_tile , field_of_view = fucade.create_FOV([lat,lon])
        data={'type': 'FeatureCollection','features': [],}
        all_hexagons = []
        for v in view:
            hexagon = {'type': 'Feature',"properties":"",'geometry': {'type': 'Polygon','coordinates': []}}
            hexagon['geometry']['coordinates'].append([li[::-1] for li in v.get_sides_4326()])
            hexagon["properties"]={"avgheight":v.get_avgHeight(),"flatness":v.flat , "points":len(v.points) , 'x':v.x , 'y':v.y}
            triangle=[]
            for t in v.triangles:
                tri={"sides":t.flatness}
                poin = []
                x_y = []
                for p in t.points:
                    poin.append(p.height)
                    x_y.append(p.pixal_xy)
                if len(poin) > 1:
                    tri['pointsMax'] = poin
                    tri['pointsMin'] = [min(poin),max(poin)]
                    tri['X_Y'] = x_y
                triangle.append(tri)
            hexagon["properties"]['triangles']=triangle
            all_hexagons.append(hexagon)
        data['features']= all_hexagons

        data2={'type': 'FeatureCollection','features': [],}
        allsquare=[]
        for v in field_of_view:
            square2 = {'type': 'Feature',"properties":"",'geometry': {'type': 'Polygon','coordinates': []}}
            square2['geometry']['coordinates'].append([li[::-1] for li in v.get_sides_4326()])
            allsquare.append(square2)
        data2['features']= allsquare


        data3 = {'type': 'FeatureCollection','features': [],}
        all_points=[]
        for p in points_tile:
            square2 = {'type': 'Feature',"properties":"",'geometry': {'type': 'Point','coordinates': []}}
            square2['geometry']['coordinates']=p.latlon[::-1]
            all_points.append(square2)
        data3['features']= all_points
        return JsonResponse({'data':data , 'square':data2 , 'data3':data3})
    return render(request,'map/map.html')

def test_fov_view(request):
    fucade = FOV_fucade() 
    fucade.test_fov()

# def model_3D(request):
#     # fucade = FOV_fucade()
#     # # [33.6933000756062,73.01716977470434]
#     # area = fucade.get_ti([33.74561028064714,73.06093707265632])
#     # area = jsonpickle.encode(area)
#     return render(request,'3D/model.html',{})