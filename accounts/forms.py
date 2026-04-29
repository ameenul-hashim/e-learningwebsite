import re
from django import forms
from .models import User
from django.core.exceptions import ValidationError

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'contact_number', 'proof_file']
        
    def clean_password(self):
        p = self.cleaned_data.get('password')
        if len(p) < 8:
            raise ValidationError("Password must be at least 8 characters.")
        if not re.search(r'[A-Z]', p):
            raise ValidationError("Must include an uppercase letter.")
        if not re.search(r'[a-z]', p):
            raise ValidationError("Must include a lowercase letter.")
        if not re.search(r'[0-9]', p):
            raise ValidationError("Must include a number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', p):
            raise ValidationError("Must include a special character.")
        return p

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 != p2:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = False # Manual approval required
        user.status = 'pending'
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}))
