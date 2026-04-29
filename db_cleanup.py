import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def force_cleanup():
    print("--- STARTING AGGRESSIVE DATABASE CLEANUP ---")
    with connection.cursor() as cursor:
        tables_to_drop = [
            'accounts_user_groups',
            'accounts_user_user_permissions',
            'accounts_user',
            'videos_video',
            'videos_subject',
            'django_migrations' # Dropping migration history entirely to force full re-run
        ]
        for table in tables_to_drop:
            try:
                print(f"Dropping table {table}...")
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            except Exception as e:
                print(f"Failed to drop {table}: {e}")
        
    print("--- CLEANUP COMPLETE ---")

if __name__ == "__main__":
    force_cleanup()
