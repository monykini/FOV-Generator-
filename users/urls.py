# from django.contrib import admin
from django.contrib.gis import admin
from django.urls import path,include
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('login',views.login_view , name='login'),
    path('logout',views.logout_view , name='logout'),
    path('registration',views.registration_view , name='registartion'),
]
