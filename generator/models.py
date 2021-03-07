from django.contrib.gis.db import models
from django.contrib.auth.models import User

#first lat than lon
buildingdata_mapping = {
    'height': 'Height',
    'geom': 'MULTIPOLYGON',
}

class cities(models.Model):
    name = models.CharField(max_length=100,unique=True,null=False)

class modelHexaGrid(models.Model):
    city = models.ForeignKey(cities,null=False,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null=False)
    wsg48center = models.PointField(unique=True)
    macpolygon = models.PolygonField(null=False)
    mac48center = models.PointField(unique=True)

class modelTiles(models.Model):
    name = models.CharField(max_length=100,unique=True,null=False)
    zoomLevel = models.PositiveIntegerField(null=False,default=15)
    rast = models.RasterField()

class modelPoint(models.Model):
    wsg48Point = models.PointField(unique=True)
    macPoint = models.PointField(unique=True)
    color = models.TextField()
    pixal_xy = models.TextField()
    height = models.FloatField()
    world_pixal_xy = models.TextField()

class buildingData(models.Model):
    height = models.FloatField()
    geom = models.MultiPolygonField(srid=4326)


class modelUserMarker(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    wsg48point = models.PointField(null=False)
    wsg48polygon = models.PolygonField(null = False)
    macpoint = models.PointField(null=False)
    macpolygon = models.PolygonField(null = False)


class modelFlatSurface(models.Model):
    marker = models.ForeignKey(modelUserMarker,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null = False)
    macpolygon = models.PolygonField(null = False)


class modelFOV(models.Model):
    flatSurface = models.ForeignKey(modelFlatSurface,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null = False)
    macpolygon = models.PolygonField(null = False)
    angel = models.FloatField(default=45)
    height = models.FloatField()

class modelHexas(models.Model):
    marker = models.ForeignKey(modelUserMarker,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null = True)
    wsg48center = models.PointField(null = True)
    macpolygon = models.PolygonField(null = True)
    maccenter = models.PointField(null = True)

