import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages

def cp_login_view(request):
    """
    Custom admin login — completely independent of Django's default admin.
    Self-healing: if the superuser doesn't exist yet, it creates it on first login.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('cp_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Step 1: Try normal Django authentication
        user = authenticate(request, username=username, password=password)

        # Step 2: If auth fails, check if credentials match env vars and self-heal
        if user is None:
            env_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
            env_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
            env_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

            if username == env_username and password == env_password and env_username and env_password:
                User = get_user_model()
                # Create user if it doesn't exist
                if not User.objects.filter(username=env_username).exists():
                    User.objects.create_superuser(
                        username=env_username,
                        email=env_email,
                        password=env_password
                    )
                    print(f"SELF-HEAL: Superuser '{env_username}' created during login")
                else:
                    # User exists but password might be wrong — reset it
                    u = User.objects.get(username=env_username)
                    u.set_password(env_password)
                    u.is_staff = True
                    u.is_superuser = True
                    u.is_verified = True
                    u.save()
                    print(f"SELF-HEAL: Password reset for '{env_username}'")

                # Try auth again
                user = authenticate(request, username=username, password=password)

        # Step 3: Log in if successful
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('cp_dashboard')
        else:
            messages.error(request, 'Invalid admin credentials.')

    return render(request, 'control_panel/login.html')


def cp_logout_view(request):
    """Log out and redirect to custom admin login."""
    logout(request)
    return redirect('cp_login')
