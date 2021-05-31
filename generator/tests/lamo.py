from django.test import TestCase , Client ,SimpleTestCase
from django.urls import reverse
from django.contrib.auth.models import User

from mixer.backend.django import mixer
import json
import datetime as dtmt


class generatorTestViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username = "admin", password = "admin",is_staff=True,is_superuser=True)
        self.client.force_login(self.admin)
    
    def grid_creation(self):
        pass

    def generator_view(self):
        pass
    

    def tile_gatherer(self):
        pass
    

    def save_Location(self):
        pass
    

    def retrieve_location(self):
        pass 


    def get_location(self):
        pass
    
    
    def delete_location(self):
        pass
        
    

