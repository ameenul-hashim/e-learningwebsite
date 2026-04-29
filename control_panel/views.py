from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import AccessRequest, User, AdminAuditLog
from videos.models import Video, Category
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from functools import wraps




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
    Main admin dashboard overview.
    """
    stats = {
        'total_users': User.objects.count(),
        'pending_requests': AccessRequest.objects.filter(status='pending').count(),
        'total_videos': Video.objects.count(),
        'total_categories': Category.objects.count(),
    }
    return render(request, 'control_panel/dashboard.html', {'stats': stats})


@cp_admin_required
def manage_requests(request):
    """
    Handle user access requests.
    """
    pending = AccessRequest.objects.filter(status='pending').order_by('-created_at')
    history = AccessRequest.objects.exclude(status='pending').order_by('-created_at')[:20]
    return render(request, 'control_panel/requests.html', {
        'pending': pending,
        'history': history
    })


@cp_admin_required
def approve_request(request, pk):
    """
    Approve an access request, automatically create a user, and notify them.
    """
    from django.utils.crypto import get_random_string
    
    access_req = get_object_or_404(AccessRequest, pk=pk)
    
    if access_req.status == 'approved':
        messages.info(request, f"Request from {access_req.email} was already approved.")
        return redirect('cp_requests')

    # Check for duplicate email
    if User.objects.filter(email=access_req.email).exists():
        access_req.status = 'approved' # Sync status anyway
        access_req.save()
        messages.warning(request, f"User with email {access_req.email} already exists. Skipping user creation.")
        return redirect('cp_requests')

    try:
        # Generate safe password and unique username
        generated_password = get_random_string(12)
        base_username = access_req.name.lower().replace(' ', '_')[:20]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Create user
        user = User.objects.create_user(
            username=username,
            email=access_req.email,
            password=generated_password,
            is_verified=True
        )
        
        access_req.status = 'approved'
        access_req.save()

        # Log action
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Approved & Created User",
            details=f"Approved {access_req.email}, Created user: {username}"
        )

        # Step 2 Email: Credentials
        subject = 'EduStream: Your Account is Ready'
        login_url = request.build_absolute_uri("/login/")
        message = (
            f"Hello {access_req.name},\n\n"
            f"Your access request to EduStream has been approved. Your account has been created successfully.\n\n"
            f"Login Credentials:\n"
            f"Username: {username}\n"
            f"Password: {generated_password}\n\n"
            f"Login here: {login_url}\n\n"
            f"Best regards,\nEduStream Team"
        )
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [access_req.email])
            messages.success(request, f"User '{username}' created and credentials sent to {access_req.email}.")
        except Exception as e:
            messages.warning(request, f"User created ({username}), but email failed to send: {str(e)}")

    except Exception as e:
        messages.error(request, f"Critical error during approval: {str(e)}")
        return redirect('cp_requests')

    return redirect('cp_requests')


@cp_admin_required
def decline_request(request, pk):
    """
    Decline an access request safely.
    """
    access_req = get_object_or_404(AccessRequest, pk=pk)
    
    if access_req.status != 'pending':
        messages.info(request, "This request has already been processed.")
        return redirect('cp_requests')

    try:
        access_req.status = 'declined'
        access_req.save()
        
        # Log action
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action="Declined Request",
            details=f"Declined request from {access_req.email}"
        )
        
        # Send rejection email
        subject = 'EduStream Access Request Update'
        message = f"Hello {access_req.name},\n\nWe regret to inform you that your access request to EduStream has been declined at this time.\n\nBest regards,\nEduStream Team"
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [access_req.email])
            messages.info(request, f"Request from {access_req.name} declined and email sent.")
        except Exception as e:
            messages.warning(request, f"Request declined, but notification email failed: {str(e)}")
            
    except Exception as e:
        messages.error(request, f"Error processing decline: {str(e)}")

    return redirect('cp_requests')


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
    Manage users (list, create, edit). Sends credentials email on creation.
    """
    users = User.objects.all().order_by('-date_joined')
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
                    
                    # Step 2 Email: Credentials
                    subject = 'EduStream: Your Login Credentials'
                    login_url = request.build_absolute_uri("/login/")
                    message = f'Hello,\n\nYour EduStream account is ready.\n\nUsername: {username}\nPassword: {password}\n\nYou can log in here: {login_url}\n\nPlease keep these credentials secure.\n\nBest regards,\nEduStream Team'
                    
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    
                    # Log admin action
                    AdminAuditLog.objects.create(
                        admin_user=request.user,
                        action="Created User",
                        details=f"Manually created user: {username} ({email})"
                    )
                    
                    messages.success(request, f"User '{username}' created and credentials sent to {email}.")

                    return redirect('cp_users')
                except Exception as e:
                    messages.error(request, f"Error creating user or sending email: {str(e)}")
        else:
            messages.error(request, "All fields are required.")
        return redirect('cp_users')

    return render(request, 'control_panel/users.html', {'users': users, 'prefill_email': prefill_email})



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

