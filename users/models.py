from django.contrib.auth.models import User
from django.contrib.gis.db import models


SIZE_CHOICES = ((0,'8px') , (1,'9px') ,(2,'10px') ,(3,'11px') )
COLOR_CHOICES = (('LM','Light Mode') , ('DM','Dark Mode') ,('CBA','Color Blind Assist',))
FONT_CHOICES = ((0,'Sans') , (1,'Caliber') ,(2,'Romans') )


class Profile(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    Font_Size = models.PositiveSmallIntegerField(choices = SIZE_CHOICES, default = '8px' )
    Color_Scheme = models.CharField(choices = COLOR_CHOICES , default = 'LM',max_length = 20)
    Font_Family =  models.PositiveSmallIntegerField(choices = FONT_CHOICES, default = 'Sans' )
    ProfileImage = models.ImageField(null=True, blank=True,upload_to='profiles/')
    Marker_Color = models.CharField(max_length = 10 , default="9d6c6c")
    Selected_Color = models.CharField(max_length = 10 , default="00ff11")
    Hotspot_Color = models.CharField(max_length = 10 , default="d50101")
# Create your models here.

class Hotspots(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    Name = models.CharField(max_length = 20)
    SpotImage = models.ImageField(null=True, blank=True,upload_to='hotspots/')
    Location = models.PointField(null = True)