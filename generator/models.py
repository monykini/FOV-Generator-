from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils import timezone
#first lat than lon
buildingdata_mapping = {
    'height': 'Height',
    'geom': 'MULTIPOLYGON',
}

# class maxElevation(models.Model):
#     tile = models.RasterField()


class cities(models.Model):
    name = models.CharField(max_length=100,unique=True,null=False)

class modelHexaGrid(models.Model):
    city = models.ForeignKey(cities,null=False,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null=False)
    wsg48center = models.PointField(unique=True)
    macpolygon = models.PolygonField(null=False)
    mac48center = models.PointField(unique=True)


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
    save_model = models.BooleanField(default=False)
    name = models.CharField(max_length=200,default='')
    created_on = models.DateTimeField(default=timezone.now())


class modelFlatSurface(models.Model):
    marker = models.ForeignKey(modelUserMarker,on_delete=models.CASCADE)
    area = models.FloatField(null=True,default=0)
    wsg48polygon = models.PolygonField(null = False)
    macpolygon = models.PolygonField(null = False)
    distance=models.FloatField(null=True,default=0)
    center = models.PointField(null=True,blank=True)
    avgHeight = models.FloatField(null=True,default=0)



class modelFOV(models.Model):
    flatSurface = models.ForeignKey(modelFlatSurface,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null = False)
    macpolygon = models.PolygonField(null = False)
    angel = models.FloatField(default=45)
    height = models.FloatField()
    sign=models.IntegerField(default=0)

class modelHexas(models.Model):
    marker = models.ForeignKey(modelUserMarker,on_delete=models.CASCADE)
    wsg48polygon = models.PolygonField(null = True)
    wsg48center = models.PointField(null = True)
    macpolygon = models.PolygonField(null = True)
    maccenter = models.PointField(null = True)

class obstructions(models.Model):
    flatSurface = models.ForeignKey(modelFlatSurface,on_delete=models.CASCADE)
    wsg48Point = models.PointField(null = True)
    macPoint = models.PointField(null = True)
    wsg48Polygon = models.PolygonField(null = True)
    height = models.FloatField(null = True)

class MLbuildingData(models.Model):
    marker = models.ForeignKey(modelUserMarker,on_delete=models.CASCADE)
    height = models.FloatField()
    geom = models.PolygonField(srid=4326)