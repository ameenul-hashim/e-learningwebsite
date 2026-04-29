from django import forms
from accounts.models import User

class AdminUserCreationForm(forms.ModelForm):
    """
    Simplified form for admin to create users. 
    Passwords are now set by the student via a secure link.
    """
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-100 rounded-2xl py-4 px-6 text-slate-900 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all font-bold placeholder:text-slate-300',
                'placeholder': 'student_id'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-100 rounded-2xl py-4 px-6 text-slate-900 focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all font-bold placeholder:text-slate-300',
                'readonly': 'readonly'
            }),
        }
