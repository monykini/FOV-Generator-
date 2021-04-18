# from django.contrib import admin
from django.contrib.gis import admin
from django.urls import path,include
from . import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index , name='homepage'),
    # path('tiles/', include('raster.urls')),
    path('Account/', include('users.urls')),
    path('generate/',include('generator.urls'))
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)