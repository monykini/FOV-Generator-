from django.shortcuts import render, redirect
from users.models import Profile, Hotspots

def index(request):	
	request.session['profile'] = Profile.objects.filter(User = request.user).values()[0]
	return render(request,'Base/index.html')