from django.shortcuts import render , redirect
from django.contrib.auth import authenticate, login , logout


from .forms import LoginForm,SignUpForm



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
            login(request, user)
            return redirect('map')
        else:
            print(form)
            return render(request,'user/registration.html',{'form':form}) 
    return render(request,'user/registration.html',{'form':form})


def logout_view(request):
    logout(request)
    return redirect('homepage')