# users/forms.py
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django import forms
from .models import Bidder

class BidderCreationForm(UserCreationForm):
    class Meta:
        model = Bidder
        fields = ('username', 'email', 'company_name', 'contact_number')

class BidderChangeForm(UserChangeForm):
    class Meta:
        model = Bidder
        fields = ('username', 'email', 'company_name', 'contact_number')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Bidder
        fields = [
            'username', 'company_name', 'contact_number', 'address',
            'tax_id', 'website', 'bio', 'avatar'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password"
    )
