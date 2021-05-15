from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.gis import geos


from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from users.models import Hotspots

from datetime import datetime
import pytz
import osmnx as ox
import json

import base64



class HotSpotSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = Hotspots
        geo_field = "Location"
        exclude = ['User']
        read_only='__all__'

    def validate_Location(self,value):
        print(value,'lmao')
        if value == None:
            raise serializers.ValidationError("Location : field is required")
        return geos.Point(tuple(value))

    def create(self, validated_data):
        print(validated_data)
        Name = validated_data.get('Name',None)
        Location = validated_data.get('Location', None)
        SpotImage = validated_data.get('SpotImage', None)
        order = Hotspots(User =self.context['request'].user,Name = Name , Location = Location , SpotImage=SpotImage)
        order.save()
        return order

    def update(self,instance, validated_data):
        print(validated_data)
        instance.Name = validated_data.get('Name',instance.Name)
        instance.Location = validated_data.get('Location', instance.Location)
        instance.SpotImage = validated_data.get('SpotImage', instance.SpotImage)
        instance.save()
        return instance