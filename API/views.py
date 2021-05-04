from django.shortcuts import render
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException

from .serializer import HotSpotSerializer
from users.models import Hotspots

import datetime as dtmt
import json
import uuid
from datetime import datetime
import pytz



class ListHoptSpots(generics.ListAPIView):
    queryset = Hotspots.objects.all()
    serializer_class = HotSpotSerializer


class ListUserHoptSpots(generics.ListAPIView):
    serializer_class = HotSpotSerializer

    def get_queryset(self):
        print(self.request.GET)
        user = self.request.user
        spots = Hotspots.objects.filter(User = user)
        return spots

class CreateHoptSpots(generics.CreateAPIView):
    serializer_class = HotSpotSerializer

    def get_serializer_context(self):
        return { 'request': self.request}

class DeleteHotSpots(generics.DestroyAPIView):
    serializer_class = HotSpotSerializer

    def destroy(self,request,id=None, *args, **kwargs):
        user = self.request.user
        queryset = Hotspots.objects.filter(User = user)
        spots = get_object_or_404(queryset, id=id)
        Hotspots.objects.get(id=id).delete()
        return Response({"delete":True})


class RetrieveHotSpot(generics.RetrieveAPIView):

    serializer_class = HotSpotSerializer

    def retrieve(self, request,id=None):
        user = self.request.user
        queryset = Hotspots.objects.filter(User = user)
        spots = get_object_or_404(queryset, id=id)
        serializer = HotSpotSerializer(spots)
        return Response(serializer.data)


class UpdateHotSpot(generics.UpdateAPIView):
    serializer_class = HotSpotSerializer

    def update(self, request,id=None):
        user = self.request.user
        queryset =  Hotspots.objects.filter(User = user)
        spot = get_object_or_404(queryset, id=id)
        serializer = HotSpotSerializer(spot , data = request.POST,partial = True,context = {"request": self.request})
        serializer.is_valid(raise_exception=True)
        sot = serializer.save()
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        return  Hotspots.objects.filter(User = user)
