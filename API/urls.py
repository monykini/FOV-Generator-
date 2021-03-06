from django.urls import path
from rest_framework.authtoken import views as vw
from . import views



urlpatterns = [

    path('api-token-auth/', vw.obtain_auth_token , name = 'obtain_api_key'),
    path('list/hotspots', views.ListHoptSpots.as_view() , name = 'listhotspots'),
    path('list/user/hotspots', views.ListUserHoptSpots.as_view() , name = 'listuserhotspots'),
    path('create/hotspots', views.CreateHoptSpots.as_view() , name = 'createhotspots'),
    path('delete/hotspots/<str:id>', views.DeleteHotSpots.as_view(), name = 'deletehotspots'),
    path('retrieve/hotspots/<str:id>', views.RetrieveHotSpot.as_view(), name = 'retrievehotspots'),
    path('update/hotspots/<str:id>', views.UpdateHotSpot.as_view(), name = 'updatehotspots'),
    path('create/fov', views.CreateLocationDetails.as_view(), name = 'createfov'),
    path('delete/fov/<str:id>', views.DeleteLocation.as_view(), name = 'deletefov'),
    path('retreive/fov/<str:id>', views.viewLocationRetreive.as_view(), name = 'retreivefov'),
    path('List/user/fov/', views.ListUserLocations.as_view(), name = 'listuserfov'),
    path('List/Points/', views. ListModelPoints.as_view(), name = 'listpoints'),


    
]