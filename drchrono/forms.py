from django import forms
from django.forms import widgets




class CheckinForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(label='Last Name', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    dob = forms.DateField(label='Date of Birth', widget=forms.TextInput(attrs={'placeholder': 'mm/dd/yyyy'}))


class UpdatePatientInfo(forms.Form):
    address = forms.CharField(label = 'Address', max_length = 300)
    phone_number = forms.CharField(label = 'Phone number', max_length = 300)
    email = forms.CharField(label = 'Email', max_length = 300)