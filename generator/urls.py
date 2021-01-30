from django.contrib import admin
from django.urls import path,include
from . import views


urlpatterns = [
    path('',views.genrator , name = 'map'),
    path('lol',views.test_fov_view , name = 'lol'),
    # path('model3d/',views.model_3D , name = '3Dmodel')

]
