import re
from django import forms
from .models import User
from django.core.exceptions import ValidationError

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'contact_number', 'proof_file']
        
    def clean_password(self):
        p = self.cleaned_data.get('password')
        if len(p) < 8: raise ValidationError("At least 8 characters required.")
        if not re.search(r'[A-Z]', p): raise ValidationError("Include an uppercase letter.")
        if not re.search(r'[a-z]', p): raise ValidationError("Include a lowercase letter.")
        if not re.search(r'[0-9]', p): raise ValidationError("Include a number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', p): raise ValidationError("Include a special character.")
        return p

    def clean(self):
        cd = super().clean()
        if cd.get('password') != cd.get('confirm_password'):
            self.add_error('confirm_password', "Passwords do not match.")
        return cd

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False
        if commit: user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
