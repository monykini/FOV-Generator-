from django.contrib.gis import admin
from .models import modelTiles,modelPoint,buildingData,cities,modelHexaGrid,modelUserMarker,modelFOV,modelFlatSurface,modelHexas,maxElevation

admin.site.register(modelTiles, admin.GeoModelAdmin)
admin.site.register(modelPoint, admin.GeoModelAdmin)
admin.site.register(buildingData, admin.GeoModelAdmin)
admin.site.register(cities, admin.GeoModelAdmin)
admin.site.register(modelHexaGrid, admin.GeoModelAdmin)
admin.site.register(modelUserMarker, admin.GeoModelAdmin)
admin.site.register(modelFOV, admin.GeoModelAdmin)
admin.site.register(modelFlatSurface, admin.GeoModelAdmin)
admin.site.register(modelHexas, admin.GeoModelAdmin)
admin.site.register(maxElevation, admin.GeoModelAdmin)


# Register your models here.
