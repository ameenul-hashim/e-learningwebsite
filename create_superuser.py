import os
import sys
from django.contrib.auth import get_user_model

def create_admin():
    # Only execute during the 'migrate' command phase
    if 'migrate' not in sys.argv:
        return

    User = get_user_model()
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if username and email and password:
        try:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                print("Superuser created")
            else:
                print("Superuser already exists")
        except Exception:
            # Handle cases where database might not be ready
            pass

if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    create_admin()
