from django.shortcuts import render , redirect
from django.contrib.auth import authenticate, login , logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .models import Profile
from .forms import LoginForm,SignUpForm,UserProfileForm,AccessibilityForm

from io import StringIO
from PIL import Image


def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST,None)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect("map")
        else:
            return render(request,'user/login.html',{'form':form}) 
    return render(request,'user/login.html',{'form':form})


def registration_view(request):
    form = SignUpForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            ProfileData = Profile.objects.Create(User = user)
            login(request, user)
            return redirect('map')
        else:
            print(form)
            return render(request,'user/registration.html',{'form':form}) 
    return render(request,'user/registration.html',{'form':form})

@login_required
def settings_view(request):
    if request.method == 'POST':
        if "accessibility" in request.POST:
            instance = Profile.objects.get(User = request.user)
            form = AccessibilityForm(request.POST, prefix="accessibility",instance = instance)
            if form.is_valid():
                AF = form.save(commit=False)
                AF.User = request.user
                AF.save()
                print('ok')
        if "profileImage" in request.POST:
            print(request.POST)
            image = request.FILES.get('myImage',None)
            filename = f"{request.user.username}.png"
            print(filename)
            instance = Profile.objects.get(User = request.user)
            instance.ProfileImage.save(filename,image,save=True)
            print(instance.ProfileImage)
            instance.save()
            print(image)


    ProfileForm = UserProfileForm(initial = User.objects.filter(email = request.user.email).values()[0],prefix='profile')
    ProfileData = Profile.objects.filter(User = request.user)[0]
    AccessForm = AccessibilityForm(initial = Profile.objects.filter(User = request.user).values()[0], prefix="accessibility")
    return render(request,'user/settings.html',  {'ProfileForm':ProfileForm , 'ProfileData': ProfileData , "AccessForm":AccessForm})



def logout_view(request):
    logout(request)
    return redirect('homepage')