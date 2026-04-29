from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name)
            user.status = 'approved'
            user.save()
            messages.success(request, "Account created! Please log in.")
            return redirect('login')
    return render(request, 'accounts/signup.html')

def logout_view(request):
    auth_logout(request)
    return redirect('login')