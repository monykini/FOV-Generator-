from django import forms
from django.core.validators import validate_email,EmailValidator
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile,SIZE_CHOICES,COLOR_CHOICES,FONT_CHOICES




class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True,widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"First Name"}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"last Name"}))
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"Username"}))
    password1 = forms.CharField(max_length=30, required=True, widget=forms.PasswordInput(attrs={'class':'form-control rounded-left',"placeholder":"Password"}))
    password2 = forms.CharField(max_length=30, required=True, widget=forms.PasswordInput(attrs={'class':'form-control rounded-left',"placeholder":"Re-Enter Password"}))
    email = forms.EmailField(max_length=254,required=True, widget=forms.EmailInput(attrs={'class':'form-control rounded-left',"placeholder":"Email"}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )

    def clean_email(self):
        value = self.cleaned_data.get('email',None)
        if EmailValidator(value):
            if User.objects.filter(email = value).exists():
                raise forms.ValidationError('Email already exists')
            return value
        raise forms.ValidationError('Enter valid E-mail')



class LoginForm(forms.Form):
    username = forms.CharField(max_length=254,required=True,widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"Username"}))
    password = forms.CharField(required=True,widget=forms.PasswordInput(attrs={'class':'form-control rounded-left',"placeholder":"Password"}))
    
    def clean(self):
 
        cleaned_data = super(LoginForm, self).clean()
         
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if len(username) < 1:
            raise forms.ValidationError('Enter correct Username')
        if not password and not username :
            raise forms.ValidationError('You have to write something!')
        user =  authenticate(username = username , password = password)

        if user == None: 
            raise forms.ValidationError('Username or Password is incorrect')

        return self.cleaned_data

class UserProfileForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True,widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"First Name" , 'disabled':True}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"last Name" , 'disabled':True}))
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control rounded-left',"placeholder":"Username" , 'disabled':True}))
    email = forms.EmailField(max_length=254,required=True, widget=forms.EmailInput(attrs={'class':'form-control rounded-left',"placeholder":"Email" , 'disabled':True}))


    
class AccessibilityForm(forms.ModelForm):
    Font_Size = forms.CharField(max_length = 20,widget=forms.Select(choices = SIZE_CHOICES,attrs={'class':'form-control rounded-left',"placeholder":"Username"}) )
    Color_Scheme = forms.CharField(max_length = 20,widget=forms.Select(choices = COLOR_CHOICES ,attrs={'class':'form-control rounded-left',"placeholder":"Username"}))
    Font_Family =  forms.CharField(max_length = 20,widget=forms.Select(choices = FONT_CHOICES,attrs={'class':'form-control rounded-left',"placeholder":"Username"}) )
    class Meta:
        model = Profile
        fields = ('Font_Family', 'Font_Size', 'Color_Scheme')

