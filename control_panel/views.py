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

def send_setup_email(username, email, password, is_reset=False):
    """
    Sends temporary credentials via Email.
    """
    action_text = "account is approved" if not is_reset else "password reset request has been processed"
    
    try:
        subject = f"EduStream: {'Login Credentials' if not is_reset else 'Reset Credentials'}"
        email_message = (
            f"Hello,\n\n"
            f"Your {action_text} 🎉\n\n"
            f"Username: {username}\n"
            f"Temporary Password: {password}\n\n"
            f"Login here: {settings.LOGIN_URL}\n\n"
            f"⚠️ You must change your username and password immediately after logging in.\n\n"
            f"Best regards,\nEduStream Team"
        )
        def send_async():
            try:
                send_mail(
                    subject, 
                    email_message, 
                    settings.DEFAULT_FROM_EMAIL, 
                    [email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Async Email Error: {str(e)}")

        import threading
        thread = threading.Thread(target=send_async)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"Email Setup Error: {str(e)}")
        return False

def send_rejection_email(email):
    """
    Sends rejection email.
    """
    try:
        def send_async():
            try:
                send_mail(
                    "EduStream Access Request",
                    "Dear Student,\n\n"
                    "Your access request was declined.\n"
                    "Reason: Submitted proof is not sufficient.\n\n"
                    "Please submit valid documents again.\n\n"
                    "Regards,\nEduStream Team",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Async Email Rejection Error: {str(e)}")
        
        import threading
        thread = threading.Thread(target=send_async)
        thread.daemon = True
        thread.start()
        return True
    except Exception as e:
        print(f"Email Rejection Setup Error: {str(e)}")
        return False




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
    Decline an access request safely via email.
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
        
        em_ok = send_rejection_email(access_req.email)

        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Request Declined",
            details=f"Declined {access_req.email}. Notification status: EM={em_ok}"
        )
        
        if em_ok:
            messages.info(request, f"Request from {access_req.name} declined and Email sent.")
        else:
            messages.error(request, "Request declined, but email notification failed.")
            
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

                # Create user with random password
                import random
                import string
                chars = string.ascii_letters + string.digits + "!@#$%"
                temp_pass = ''.join(random.choice(chars) for _ in range(10))
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=temp_pass,
                    is_verified=True,
                    is_blocked=False,
                    whatsapp_number=normalize_phone(access_req.whatsapp)
                )
                user.must_change_password = True
                user.onboarding_completed = False
                user.save()
                
                # Send Email
                em_ok = send_setup_email(username, email, temp_pass)
                
                if em_ok:
                    messages.success(request, f"Account created and Login Credentials sent via Email.")
                else:
                    messages.error(request, "Account created, but Email notification failed.")

                AdminAuditLog.objects.create(
                    admin_user=request.user,
                    action="User Onboarded",
                    details=f"Finalized account for {access_req.email}. Username: {username}."
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
    Generate a new temporary password and send via email.
    """
    user = get_object_or_404(User, pk=pk)
    
    if user.onboarding_completed:
        messages.info(request, f"User {user.username} has already completed onboarding.")
        return redirect('cp_users')

    try:
        import random
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        temp_pass = ''.join(random.choice(chars) for _ in range(10))
        
        user.set_password(temp_pass)
        user.must_change_password = True
        user.save()
        
        em_ok = send_setup_email(user.username, user.email, temp_pass, is_reset=True)
        
        if em_ok:
            messages.success(request, f"New login credentials sent to {user.email}.")
        else:
            messages.error(request, "Failed to send new credentials via Email.")

        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Resent Credentials",
            details=f"Generated new temporary password for {user.email}."
        )
        
    except Exception as e:
        messages.error(request, f"Error resending credentials: {str(e)}")
        
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

