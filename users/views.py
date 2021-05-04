from django.shortcuts import render , redirect
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.gis import geos
from django.http import JsonResponse

from .models import Profile,Hotspots
from .forms import LoginForm,SignUpForm,UserProfileForm,AccessibilityForm

from io import StringIO
from PIL import Image
from pyproj import Transformer
import shapely
import json

def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST,None)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("map")
        else:
            return render(request,'user/login.html',{'form':form}) 
    return render(request,'user/login.html',{'form':form})


def registration_view(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            ProfileData = Profile.objects.Create(User = user)
            ProfileData.save()
            login(request, user)
            return redirect('map')
        else:
            return render(request,'user/registration.html',{'form':form}) 
    return render(request,'user/registration.html',{'form':form})

@login_required
def settings_view(request):
    if request.method == 'POST':
        if "accessibility" in request.POST:
            instance = Profile.objects.get(User = request.user)
            form = AccessibilityForm(request.POST, prefix="accessibility",instance = instance)
            if form.is_valid():
                AF = form.save(commit=False)
                AF.User = request.user
                AF.save()
        if "profileImage" in request.POST:
            image = request.FILES.get('myImage',None)
            filename = f"{request.user.username}.png"
            instance = Profile.objects.get(User = request.user)
            instance.ProfileImage.save(filename,image,save=True)
            instance.save()

    hotspots = HotSpot.objects.get(User = request.user)
    ProfileForm = UserProfileForm(initial = User.objects.filter(email = request.user.email).values()[0],prefix='profile')
    ProfileData = Profile.objects.filter(User = request.user)[0]
    AccessForm = AccessibilityForm(initial = Profile.objects.filter(User = request.user).values()[0], prefix="accessibility")
    return render(request,'user/settings.html',  {'ProfileForm':ProfileForm , 'ProfileData': ProfileData , "AccessForm":AccessForm, "hotspots":hotspots})



def logout_view(request):
    logout(request)
    return redirect('homepage')


def save_hotspots(request):
    if request.method == 'POST':
        name = request.POST.get('name',None)
        location = request.POST.get('location',None)
        image = request.FILES.get('spotImage',None)
        filename = f"{request.user.username}.png"
        instance = HotSpot.objects.create(User = request.user,Name = name,Location = tuple(location))
        instance.ProfileImage.save(filename,image,save=True)
        instance.save()
        return JsonResponse({"status":'ok'})
    return JsonResponse({"status":'ok'},status = 400)

def retrieve_hotspot(request,id):
    instance = HotSpot.objects.get(User = request.user,id = id)
    return JsonResponse({"name":instance.Name , "location":instance.location , 'spotimage':instance.SpotImage.url})

def list_user_hotspots(request):
    instance = HotSpot.objects.get(User = request.user).values()
    return jsonResponse({"hotspots":instance})

def list_location_hotspots(request):
    if request.method == 'POST':
        print(request.POST)
        location = json.loads(request.POST.get('hotspotlonlat',None))
        print(location)
        area = float(request.POST.get('hotspotarea',200))

        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")

        x2,y2 = transformer.transform(location[0], location[1])
        point = shapely.geometry.Point(x2,y2)
        og_circle = point.buffer(area)

        transformer = Transformer.from_crs("epsg:3857" , "epsg:4326")

        square_4326 = []
        for p in list(og_circle.exterior.coords):
            x,y = transformer.transform(p[0], p[1])
            square_4326.append([y,x])
        circle = geos.Polygon(tuple(square_4326)[:])
        print(circle)
        instance = Hotspots.objects.filter(Location__intersects = circle )

        allHotSpots={"type": "FeatureCollection","features": []}
        for hot in instance:
            hotspot = {'type': 'Feature',"properties":"",'geometry': json.loads(hot.Location.geojson)}
            hotspot['properties'] = {'name':hot.Name , 'hotspotimage':hot.SpotImage.url}
            allHotSpots['features'].append(hotspot)
        
        
        return JsonResponse(allHotSpots)
    return JsonResponse({"status":'not ok'},status = 400)
    
