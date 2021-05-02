from django.contrib.gis import admin

from .models import Profile,Hotspots

admin.site.register(Profile)
admin.site.register(Hotspots, admin.GeoModelAdmin)
# Register your models here.
