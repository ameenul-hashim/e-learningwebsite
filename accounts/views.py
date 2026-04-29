from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, LoginForm
from .models import User

def landing_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Admins bypass approval constraints
                if user.is_staff:
                    login(request, user)
                    return redirect('admin_dashboard')
                
                # Student approval logic
                if user.status == 'blocked':
                    messages.error(request, "Your account has been blocked. Please contact support.")
                elif user.status == 'pending' or not user.is_active:
                    messages.warning(request, "Your account is currently under verification by our team.")
                else:
                    login(request, user)
                    return redirect('dashboard')
            else:
                messages.error(request, "The credentials provided do not match our records.")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Signup successful! Your account is pending approval.")
            return redirect('login')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')