from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm, LoginForm
from .models import User

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                if user.is_staff:
                    login(request, user); return redirect('admin_dashboard')
                if user.status == 'blocked':
                    messages.error(request, "You are blocked.")
                elif not user.is_active:
                    messages.warning(request, "Verification pending.")
                else:
                    login(request, user); return redirect('dashboard')
            else:
                messages.error(request, "Invalid credentials.")
    else: form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Application submitted for verification.")
            return redirect('login')
    else: form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def logout_view(request):
    logout(request); return redirect('login')
