import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import AccessRequest, User, AdminAuditLog
from videos.models import Video, Category
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from functools import wraps
from twilio.rest import Client

def normalize_phone(phone):
    """
    Ensure phone number has '+' and country code. Defaults to +91 if missing.
    """
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if not clean_phone.startswith('91') and len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}"
    if not clean_phone.startswith('+'):
        clean_phone = f"+{clean_phone}"
    return clean_phone

def send_whatsapp_notification(to_number, message_body):
    """
    Helper to send WhatsApp messages via Twilio with validation.
    """
    try:
        normalized_to = normalize_phone(to_number)
        
        # Twilio sandbox requires the number to be prefixed with 'whatsapp:'
        formatted_to = f"whatsapp:{normalized_to}"
            
        client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'), 
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        client.messages.create(
            from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
            body=message_body,
            to=formatted_to
        )
        return True
    except Exception as e:
        print(f"Twilio Send Error: {str(e)}")
        return False

def send_credential_notification(user_name, email, whatsapp, username, password, is_reset=False):
    """
    Primary WhatsApp delivery with Email Fallback.
    """
    login_url = settings.LOGIN_URL # or build absolute
    action_text = "application is approved" if not is_reset else "credentials have been reset"
    pass_label = "Password" if not is_reset else "New Password"
    
    message_body = (
        f"EduStream: Your {action_text}.\n"
        f"Username: {username}\n"
        f"{pass_label}: {password}\n"
        f"Do not share this information."
    )
    
    # Try WhatsApp
    whatsapp_success = send_whatsapp_notification(whatsapp, message_body)
    
    # Try Email anyway or as fallback
    email_success = False
    try:
        subject = f"EduStream: {'Account Ready' if not is_reset else 'Password Reset'}"
        email_message = (
            f"Hello {user_name},\n\n"
            f"Your {action_text}.\n\n"
            f"Username: {username}\n"
            f"{pass_label}: {password}\n\n"
            f"Keep these credentials secure.\n\n"
            f"Best regards,\nEduStream Team"
        )
        send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [email])
        email_success = True
    except Exception as e:
        print(f"Email Error: {str(e)}")
        
    return whatsapp_success, email_success




def cp_admin_required(view_func):
    """
    Custom decorator: redirects to /control-panel/login/ if not staff.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('cp_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@cp_admin_required
def dashboard(request):
    """
    Main admin dashboard overview with audit logs.
    """
    stats = {
        'total_users': User.objects.count(),
        'pending_requests': AccessRequest.objects.filter(status='pending').count(),
        'total_videos': Video.objects.count(),
        'total_categories': Category.objects.count(),
    }
    recent_logs = AdminAuditLog.objects.select_related('admin_user').all()[:10]
    return render(request, 'control_panel/dashboard.html', {
        'stats': stats,
        'recent_logs': recent_logs
    })


@cp_admin_required
def manage_requests(request):
    """
    Handle user access requests with pagination.
    """
    from django.core.paginator import Paginator
    pending_list = AccessRequest.objects.filter(status='pending').order_by('-created_at')
    
    paginator = Paginator(pending_list, 10) # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    history = AccessRequest.objects.exclude(status='pending').order_by('-created_at')[:20]
    return render(request, 'control_panel/requests.html', {
        'pending': page_obj,
        'history': history
    })


@cp_admin_required
def approve_request(request, pk):
    """
    Step 1: Approve an access request and redirect to user creation.
    """
    access_req = get_object_or_404(AccessRequest, pk=pk)
    
    if access_req.status == 'approved':
        messages.info(request, "This request is already approved.")
        return redirect('cp_requests')

    try:
        access_req.status = 'approved'
        access_req.save()
        
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Approved Request (Step 1)",
            details=f"Approved access for {access_req.email}"
        )
        
        messages.success(request, f"Request for {access_req.name} approved. Please complete account creation.")
        return redirect('cp_create_user_from_request', request_id=access_req.pk)
        
    except Exception as e:
        messages.error(request, f"Error approving request: {str(e)}")
        return redirect('cp_requests')


@cp_admin_required
def decline_request(request, pk):
    """
    Decline an access request safely with custom message.
    """
    access_req = get_object_or_404(AccessRequest, pk=pk)
    
    if access_req.status != 'pending':
        messages.info(request, "This request has already been processed.")
        return redirect('cp_requests')

    try:
        access_req.status = 'declined'
        access_req.save()
        
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Declined Request",
            details=f"Declined request from {access_req.email}"
        )
        
        # Send WhatsApp rejection message
        message_body = (
            f"Dear {access_req.name}, your access to EduStream is declined. "
            "Your submitted proof is not sufficient. Please upload a valid document."
        )
        
        ws_ok = send_whatsapp_notification(access_req.whatsapp, message_body)
        
        # Email fallback for rejection
        em_ok = False
        if not ws_ok:
            try:
                subject = "EduStream: Access Request Update"
                email_message = (
                    f"Hello {access_req.name},\n\n"
                    "We regret to inform you that your verification proof was not sufficient for access.\n"
                    "Please log in to the landing page and submit a valid student ID or document.\n\n"
                    "Best regards,\nEduStream Team"
                )
                send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [access_req.email])
                em_ok = True
            except Exception as e:
                print(f"Email Rejection Error: {str(e)}")

        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Request Declined",
            details=f"Declined {access_req.email}. Notification status: WS={ws_ok}, EM={em_ok}"
        )
        
        if ws_ok:
            messages.info(request, f"Request from {access_req.name} declined and WhatsApp sent.")
        elif em_ok:
            messages.warning(request, f"WhatsApp failed, but rejection Email sent to {access_req.email}.")
        else:
            messages.error(request, "Request declined, but both notification methods failed.")
            
    except Exception as e:
        messages.error(request, f"Error processing decline: {str(e)}")

    return redirect('cp_dashboard')


@cp_admin_required
def create_user_from_request(request, request_id):
    """
    Step 2: Dedicated page to create user from an approved request.
    """
    from .forms import AdminUserCreationForm
    access_req = get_object_or_404(AccessRequest, pk=request_id)
    
    if access_req.status != 'approved':
        messages.error(request, "This request must be approved before creating a user.")
        return redirect('cp_requests')

    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data['username']
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                
                # Double check existence (forms.ModelForm handles some, but let's be safe)
                if User.objects.filter(email=email).exists():
                    messages.error(request, f"User with email {email} already exists.")
                    return render(request, 'control_panel/create_user_from_request.html', {'form': form, 'req': access_req})

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_verified=True,
                    whatsapp_number=normalize_phone(access_req.whatsapp)
                )
                
                # Send Credentials with Fallback
                ws_ok, em_ok = send_credential_notification(
                    access_req.name, access_req.email, access_req.whatsapp, 
                    username, password
                )
                
                if ws_ok:
                    messages.success(request, f"Account created and WhatsApp sent to {access_req.whatsapp}.")
                elif em_ok:
                    messages.warning(request, f"Account created. WhatsApp failed, but fallback Email sent to {access_req.email}.")
                else:
                    messages.error(request, "Account created, but both WhatsApp and Email notifications failed.")

                AdminAuditLog.objects.create(
                    admin_user=request.user,
                    action="User Onboarded",
                    details=f"Finalized account for {access_req.email}. Username: {username}. Notification status: WS={ws_ok}, EM={em_ok}"
                )
                return redirect('cp_dashboard')
                
            except Exception as e:
                messages.error(request, f"Database error during user creation: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = AdminUserCreationForm(initial={'email': access_req.email})
        
    return render(request, 'control_panel/create_user_from_request.html', {
        'form': form,
        'req': access_req
    })


@cp_admin_required
def resend_credentials(request, pk):
    """
    Reset password and resend credentials via WhatsApp.
    """
    from django.utils.crypto import get_random_string
    user = get_object_or_404(User, pk=pk)
    
    if not user.whatsapp_number:
        messages.error(request, f"User {user.username} does not have a WhatsApp number on file.")
        return redirect('cp_users')

    try:
        # Generate new password
        new_password = get_random_string(12)
        user.set_password(new_password)
        user.save()
        
        ws_ok, em_ok = send_credential_notification(
            user.username, user.email, user.whatsapp_number, 
            user.username, new_password, is_reset=True
        )
        
        if ws_ok:
            messages.success(request, f"New credentials sent to {user.username} via WhatsApp.")
        elif em_ok:
            messages.warning(request, f"WhatsApp failed, but new credentials sent via Email fallback.")
        else:
            messages.error(request, "Failed to send new credentials via both WhatsApp and Email.")

        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Credentials Reset",
            details=f"Reset and resent credentials for {user.username}. Notification status: WS={ws_ok}, EM={em_ok}"
        )
            
    except Exception as e:
        messages.error(request, f"Error resetting credentials: {str(e)}")

    return redirect('cp_users')


@cp_admin_required
def manage_videos(request):
    """
    Manage video catalog.
    """
    videos = Video.objects.select_related('category').all().order_by('-created_at')
    categories = Category.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        youtube_url = request.POST.get('youtube_url')
        category_id = request.POST.get('category')

        if title and youtube_url:
            category = Category.objects.get(id=category_id) if category_id else None
            Video.objects.create(
                title=title,
                youtube_url=youtube_url,
                category=category
            )
            
            # Invalidate Dashboard Cache
            cache.clear()
            
            # Log admin action
            AdminAuditLog.objects.create(
                admin_user=request.user,
                action="Added Video",
                details=f"Added video: {title}"
            )
            
            messages.success(request, f"Video '{title}' added successfully.")
            return redirect('cp_videos')


    return render(request, 'control_panel/videos.html', {
        'videos': videos,
        'categories': categories
    })


@cp_admin_required
def delete_video(request, pk):
    """
    Delete a video.
    """
    video = get_object_or_404(Video, pk=pk)
    title = video.title
    video.delete()
    
    # Invalidate Dashboard Cache
    cache.clear()
    
    # Log admin action
    AdminAuditLog.objects.create(
        admin_user=request.user,
        action="Deleted Video",
        details=f"Deleted video: {title}"
    )
    
    messages.warning(request, "Video removed.")

    return redirect('cp_videos')


@cp_admin_required
def manage_users(request):
    """
    Manage users (list, create, edit) with pagination.
    """
    from django.core.paginator import Paginator
    
    user_list = User.objects.all().order_by('-date_joined')
    paginator = Paginator(user_list, 15) # 15 per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    prefill_email = request.session.pop('prefill_email', '')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if username and email and password:
            if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
                messages.error(request, "User with this username or email already exists.")
            else:
                try:
                    user = User.objects.create_user(
                        username=username, 
                        email=email, 
                        password=password, 
                        is_verified=True
                    )
                    
                    # Log admin action
                    AdminAuditLog.objects.create(
                        admin_user=request.user,
                        action="Created User",
                        details=f"Manually created user: {username} ({email})"
                    )
                    
                    messages.success(request, f"User '{username}' created. Please use the 'Resend Credentials' tool to send details via WhatsApp if needed.")

                    return redirect('cp_users')
                except Exception as e:
                    messages.error(request, f"Error creating user: {str(e)}")
        else:
            messages.error(request, "All fields are required.")
        return redirect('cp_users')

    return render(request, 'control_panel/users.html', {
        'users': page_obj, 
        'prefill_email': prefill_email
    })



@cp_admin_required
def delete_user(request, pk):
    """
    Delete a user.
    """
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Cannot delete superuser.")
    else:
        username = user.username
        user.delete()
        
        # Log admin action
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Deleted User",
            details=f"Deleted user account: {username}"
        )
        
        messages.warning(request, "User deleted.")

    return redirect('cp_users')


@cp_admin_required
def toggle_user_status(request, pk):
    """
    Block/Activate a user.
    """
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Cannot modify superuser status.")
    else:
        user.is_blocked = not user.is_blocked
        user.is_active = not user.is_blocked
        user.save()
        status = "blocked" if user.is_blocked else "activated"
        
        # Log admin action
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action=f"{status.capitalize()} User",
            details=f"Changed status for {user.username} to {status}"
        )
        
        messages.success(request, f"User {user.username} has been {status}.")

    return redirect('cp_users')


@cp_admin_required
def manage_categories(request):
    """
    Manage categories/subjects.
    """
    categories = Category.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            Category.objects.create(name=name, description=description)
            
            # Invalidate Dashboard Cache
            cache.clear()
            
            # Log admin action
            AdminAuditLog.objects.create(
                admin_user=request.user,
                action="Added Subject",
                details=f"Added subject: {name}"
            )
            
            messages.success(request, f"Subject '{name}' added successfully.")
            return redirect('cp_categories')


    return render(request, 'control_panel/categories.html', {'categories': categories})


@cp_admin_required
def delete_category(request, pk):
    """
    Delete a category/subject.
    """
    category = get_object_or_404(Category, pk=pk)
    name = category.name
    category.delete()
    
    # Invalidate Dashboard Cache
    cache.clear()
    
    # Log admin action
    AdminAuditLog.objects.create(
        admin_user=request.user,
        action="Deleted Subject",
        details=f"Deleted subject: {name}"
    )
    
    messages.warning(request, "Subject deleted.")

    return redirect('cp_categories')

