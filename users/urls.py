# from django.contrib import admin
from django.contrib.gis import admin
from django.urls import path,include
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('login',views.login_view , name='login'),
    path('logout',views.logout_view , name='logout'),
    path('registration',views.registration_view , name='registartion'),
    path('settings',views.settings_view , name='settings'),
    path('save/hotspot',views.save_hotspots , name='savehotspot'),
    path('list/location/hotspots',views.list_location_hotspots , name='listlocationhotspots'),
]
