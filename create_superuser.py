import os
import django
from django.db.utils import OperationalError, ProgrammingError

def run():
    # Only run if credentials are provided
    username = os.getenv('DJANGO_SUPERUSER_USERNAME')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
    
    if not all([username, email, password]):
        return

    try:
        # We don't call django.setup() here because manage.py will handle it 
        # or we are being called within a context where it's ready/being readied.
        # However, to use the models, we need the app registry to be ready.
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"AUTOMATION: Superuser '{username}' created successfully.")
        else:
            # Silence this in production to keep logs clean, or keep for verification
            pass
    except (OperationalError, ProgrammingError):
        # This happens if migrations haven't been run yet (e.g. first deploy)
        # We simply skip and it will succeed on the next run (e.g. after migrate)
        pass
    except Exception as e:
        print(f"AUTOMATION ERROR: Could not create superuser: {e}")

if __name__ == "__main__":
    # If run directly, we need setup
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    run()
