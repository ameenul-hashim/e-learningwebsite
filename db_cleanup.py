import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def fix_db():
    with connection.cursor() as cursor:
        print("Checking for schema consistency...")
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app IN ('accounts', 'videos', 'control_panel');")
            cursor.execute("DROP TABLE IF EXISTS accounts_user CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS videos_video CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS videos_subject CASCADE;")
            print("Legacy tables dropped for fresh rebuild.")
        except Exception as e:
            print(f"Cleanup note: {e}")

if __name__ == "__main__":
    fix_db()
