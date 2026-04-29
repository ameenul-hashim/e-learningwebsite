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
# from twilio.rest import Client
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

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
    return False
    # try:
    #     normalized_to = normalize_phone(to_number)
    #     
    #     # Twilio sandbox requires the number to be prefixed with 'whatsapp:'
    #     formatted_to = f"whatsapp:{normalized_to}"
    #         
    #     client = Client(
    #         os.getenv('TWILIO_ACCOUNT_SID'), 
    #         os.getenv('TWILIO_AUTH_TOKEN')
    #     )
    #     
    #     client.messages.create(
    #         from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
    #         body=message_body,
    #         to=formatted_to
    #     )
    #     return True
    # except Exception as e:
    #     print(f"Twilio Send Error: {str(e)}")
    #     return False

def send_credential_notification(user_name, email, whatsapp, username, setup_link, is_reset=False):
    """
    Sends a secure password setup link via WhatsApp with Email Fallback.
    """
    action_text = "account is approved" if not is_reset else "password reset request has been processed"
    
    message_body = (
        f"EduStream: Your {action_text}.\n"
        f"Username: {username}\n"
        f"Set your password here: {setup_link}\n"
        f"This link expires soon."
    )
    
    # Try WhatsApp
    whatsapp_success = send_whatsapp_notification(whatsapp, message_body)
    
    # Try Email anyway or as fallback
    email_success = False
    try:
        subject = f"EduStream: {'Set Your Password' if not is_reset else 'Reset Your Password'}"
        email_message = (
            f"Hello {user_name},\n\n"
            f"Your {action_text}.\n\n"
            f"Username: {username}\n\n"
            f"Please click the link below to set your secure password:\n"
            f"{setup_link}\n\n"
            f"This link is valid for a limited time.\n\n"
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
    Main admin dashboard overview with advanced analytics.
    """
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    from videos.models import VideoWatchLog

    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    stats = {
        'total_users': User.objects.count(),
        'pending_requests': AccessRequest.objects.filter(status='pending').count(),
        'total_videos': Video.objects.count(),
        'total_categories': Category.objects.count(),
        'active_users': User.objects.filter(last_active__gte=thirty_days_ago).count(),
    }
    
    # Analytics
    top_subjects = Category.objects.annotate(
        watch_count=Count('videos__videowatchlog')
    ).order_by('-watch_count')[:5]
    
    top_videos = Video.objects.annotate(
        watch_count=Count('videowatchlog')
    ).order_by('-watch_count')[:5]

    recent_logs = AdminAuditLog.objects.select_related('admin_user').all()[:10]
    
    return render(request, 'control_panel/dashboard.html', {
        'stats': stats,
        'recent_logs': recent_logs,
        'top_subjects': top_subjects,
        'top_videos': top_videos,
    })


@cp_admin_required
def manage_requests(request):
    """
    Handle user access requests with search, filter, and pagination.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    pending_list = AccessRequest.objects.filter(status='pending')
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        pending_list = pending_list.filter(
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(whatsapp__icontains=search_query)
        )
    
    pending_list = pending_list.order_by('-created_at')
    
    paginator = Paginator(pending_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # History with status filter
    status_filter = request.GET.get('status')
    history = AccessRequest.objects.exclude(status='pending')
    if status_filter in ['approved', 'rejected']:
        history = history.filter(status=status_filter)
    
    history = history.order_by('-created_at')[:20]
    
    return render(request, 'control_panel/requests.html', {
        'pending': page_obj,
        'history': history,
        'search_query': search_query,
        'status_filter': status_filter
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
        access_req.status = 'rejected'
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
                
                if User.objects.filter(email=email).exists():
                    messages.error(request, f"User with email {email} already exists.")
                    return render(request, 'control_panel/create_user_from_request.html', {'form': form, 'req': access_req})

                # Create user with random password (never sent)
                from django.utils.crypto import get_random_string
                temp_pass = get_random_string(32)
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=temp_pass,
                    is_verified=True,
                    is_blocked=False,
                    whatsapp_number=normalize_phone(access_req.whatsapp)
                )
                user.must_change_password = True
                user.save()
                
                # Generate Password Setup Link
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                setup_link = f"{request.build_absolute_uri('/')[:-1]}/accounts/setup-password/{uid}/{token}/"
                
                # Send Link with Fallback
                ws_ok, em_ok = send_credential_notification(
                    access_req.name, access_req.email, access_req.whatsapp, 
                    username, setup_link
                )
                
                if ws_ok:
                    messages.success(request, f"Account created and Setup Link sent to WhatsApp.")
                elif em_ok:
                    messages.warning(request, f"Account created. WhatsApp failed, but Setup Link sent via Email.")
                else:
                    messages.error(request, "Account created, but both WhatsApp and Email notifications failed.")

                AdminAuditLog.objects.create(
                    admin_user=request.user,
                    action="User Onboarded",
                    details=f"Finalized account for {access_req.email}. Username: {username}. Link sent."
                )
                return redirect('cp_dashboard')
                
            except Exception as e:
                messages.error(request, f"Database error during user creation: {str(e)}")
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = AdminUserCreationForm(initial={'email': access_req.email})
        
    return render(request, 'control_panel/create_user_from_request.html', {
        'form': form,
        'req': access_req
    })


@cp_admin_required
def resend_setup_link(request, pk):
    """
    Generate and resend a secure password setup link.
    """
    user = get_object_or_404(User, pk=pk)
    
    if user.onboarding_completed:
        messages.info(request, f"User {user.username} has already completed onboarding.")
        return redirect('cp_users')

    if not user.whatsapp_number:
        messages.error(request, f"User {user.username} does not have a WhatsApp number on file.")
        return redirect('cp_users')

    try:
        # Generate fresh token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        setup_link = f"{request.build_absolute_uri('/')[:-1]}/accounts/setup-password/{uid}/{token}/"
        
        # Send Link with Fallback
        ws_ok, em_ok = send_credential_notification(
            user.username, user.email, user.whatsapp_number, 
            user.username, setup_link, is_reset=True
        )
        
        if ws_ok or em_ok:
            messages.success(request, f"Fresh setup link sent to {user.username} via {'WhatsApp' if ws_ok else 'Email'}.")
        else:
            messages.error(request, "Failed to send setup link via both channels.")

        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Resent Setup Link",
            details=f"Generated new setup token for {user.email}."
        )
        
    except Exception as e:
        messages.error(request, f"Error resending link: {str(e)}")
        
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
    Manage users (list, create, edit) with search and pagination.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    user_list = User.objects.all()
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        user_list = user_list.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(whatsapp_number__icontains=search_query)
        )
    
    user_list = user_list.order_by('-date_joined')
    paginator = Paginator(user_list, 15)
    
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

