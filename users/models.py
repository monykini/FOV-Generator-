from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.db.models.signals import pre_save,post_save,post_delete , pre_delete
from rest_framework.authtoken.models import Token
from django.dispatch import receiver
from django.utils import timezone

import os

SIZE_CHOICES = ((0,'8px') , (1,'9px') ,(2,'10px') ,(3,'11px') )
COLOR_CHOICES = (('LM','Light Mode') , ('DM','Dark Mode') ,('CBA','Color Blind Assist',))
FONT_CHOICES = ((0,'Sans') , (1,'Caliber') ,(2,'Romans') )


class Profile(models.Model):
    User = models.ForeignKey(User, on_delete=models.CASCADE)
    Font_Size = models.PositiveSmallIntegerField(choices = SIZE_CHOICES, default = 0 )
    Color_Scheme = models.CharField(choices = COLOR_CHOICES , default = 'LM',max_length = 20)
    Font_Family =  models.PositiveSmallIntegerField(choices = FONT_CHOICES, default = 0 )
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
    Created = models.DateTimeField(default=timezone.now())

@receiver(post_save, sender=Profile)
def create_token(sender, instance,created, **kwargs):
    if created:
        obj = Token.objects.get_or_create(user = instance.User)
        path = f"userRasters/{instance.User.username}"
        os.mkdir(path)
