from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import AccessRequest
from .forms import AccessRequestForm, CustomLoginForm

def landing_page(request):
    """
    Landing page with access request form.
    """
    if request.method == 'POST':
        form = AccessRequestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Your request has been submitted successfully. We will contact you soon.")
            return redirect('landing')
    else:
        form = AccessRequestForm()
    return render(request, 'accounts/landing.html', {'form': form})

class RestrictedLoginView(LoginView):
    """
    Custom login view that checks if user is verified and not blocked.
    """
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_verified:
            messages.error(self.request, "Access denied: Your account is not verified.")
            return self.form_invalid(form)
        if user.is_blocked:
            messages.error(self.request, "Access denied: Your account is blocked.")
            return self.form_invalid(form)
        
        auth_login(self.request, user)
        return redirect(self.get_success_url())
