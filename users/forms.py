from django import forms
from django.core.validators import validate_email,EmailValidator
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User




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