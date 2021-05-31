from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.gis import geos


from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework.parsers import MultiPartParser
from rest_framework.parsers import FormParser
from rest_framework.parsers import FileUploadParser
from rest_framework.parsers import JSONParser
from users.models import Hotspots
from generator.models import modelUserMarker,modelPoint

from datetime import datetime
import pytz
import osmnx as ox
import json

import base64

class ModelPointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = modelPoint
        geo_field = "wsg48Point"
        fields = ['id']
        read_only='__all__'


class HotSpotSerializer(GeoFeatureModelSerializer):

    parser_classes = (FormParser,JSONParser,MultiPartParser,FileUploadParser,)
    serializer_class = (FormParser,JSONParser,MultiPartParser,FileUploadParser,)

    class Meta:
        model = Hotspots
        geo_field = "Location"
        exclude = ['User']
        read_only='__all__'

    def validate_Location(self,value):
        print(value,'lmao')
        # print(value,'lmao')
        if value == None:
            raise serializers.ValidationError("Location : field is required")
        return geos.Point(tuple(value))

    def create(self, validated_data):
        print(validated_data,'lmao')
        Name = validated_data.get('Name',None)
        Location = validated_data.get('Location', None)
        SpotImage = validated_data.get('SpotImage', None)
        order = Hotspots(User =self.context['request'].user,Name = Name , Location = Location , SpotImage=SpotImage)
        order.save()
        return order

    def update(self,instance, validated_data):
        print(self.context,'lmao')
        instance.Name = validated_data.get('Name',instance.Name)
        instance.Location = validated_data.get('Location', instance.Location)
        instance.SpotImage = self.context['files'].get('SpotImage', instance.SpotImage)
        instance.save()
        return instance


class LocationSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = modelUserMarker
        geo_field = "wsg48point"
        fields = ['id','name','created_on']
        read_only='__all__'