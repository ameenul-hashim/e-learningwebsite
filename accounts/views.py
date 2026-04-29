from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import AccessRequest
from .forms import AccessRequestForm, CustomLoginForm
# from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from .models import User

def password_setup_view(request, uidb64, token):
    """
    View for students to set their password for the first time using a secure link.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Block if onboarding already completed
    if user and user.onboarding_completed:
        messages.info(request, "Your account setup is already complete. Please log in.")
        return redirect('login')

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
            else:
                import re
                if len(password) < 8:
                    messages.error(request, "Password must be at least 8 characters.")
                elif not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password):
                    messages.error(request, "Password must include uppercase and numbers.")
                else:
                    user.set_password(password)
                    user.must_change_password = False
                    user.onboarding_completed = True
                    user.save()
                    
                    # Auto-login after successful setup
                    auth_login(request, user)
                    messages.success(request, "Password set successfully! Welcome to your dashboard.")
                    return redirect('dashboard')
        
        return render(request, 'accounts/password_setup.html', {'user': user, 'valid': True})
    else:
        return render(request, 'accounts/password_setup.html', {'valid': False})

def landing_page(request):
    """
    Landing page with access request form.
    """
    if request.method == 'POST':
        form = AccessRequestForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Your request has been submitted successfully. We will contact you soon.")
                return redirect('landing')
            except Exception as e:
                messages.error(request, f"An error occurred while saving your proof: {str(e)}. Please try again or contact support.")
        else:
            messages.error(request, "Please correct the errors in the form before submitting.")
    else:
        form = AccessRequestForm()
    return render(request, 'accounts/landing.html', {'form': form})

class RestrictedLoginView(LoginView):
    """
    Custom login view that checks if user is verified and not blocked.
    """
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'

    # @method_decorator(ratelimit(key='ip', rate='5/m', block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_verified:
            messages.error(self.request, "Access denied: Your account is not verified.")
            return self.form_invalid(form)
        if user.is_blocked:
            messages.error(self.request, "Access denied: Your account is blocked.")
            return self.form_invalid(form)
        
        try:
            auth_login(self.request, user)
            
            # Forced Password Change Logic
            if user.must_change_password:
                messages.info(self.request, "For your security, please change your temporary password before continuing.")
                return redirect('force_password_change')
                
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"Login failed due to a server error: {str(e)}.")
            return self.form_invalid(form)

@login_required
def force_password_change(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        else:
            from control_panel.forms import AdminUserCreationForm
            form = AdminUserCreationForm(data={
                'username': request.user.username, 
                'email': request.user.email, 
                'password': password
            })
            if form.is_valid():
                request.user.set_password(password)
                request.user.must_change_password = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password updated successfully!')
                return redirect('dashboard')
            else:
                for error in form.errors.values():
                    messages.error(request, error[0])
    return render(request, 'accounts/force_password_change.html')