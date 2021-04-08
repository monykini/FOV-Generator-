from django.contrib import admin
from django.urls import path,include
from . import views


urlpatterns = [
    path('',views.genrator , name = 'map'),
    path('model/',views.model , name = 'model'),
    # path('processBuildingData',views.processBuildingData , name = 'processBuildingData'),
    # path('processHexaGrid',views.processHexaGrid , name = 'processHexaGrid'),

]
