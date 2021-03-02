from django.contrib import admin
from django.urls import path,include
from . import views


urlpatterns = [
    path('',views.genrator , name = 'map'),
    # path('processData',views.processData , name = 'processData'),

]
