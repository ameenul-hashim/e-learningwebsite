import os; import django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings'); django.setup(); from django.db import connection; 
with connection.cursor() as cursor:
    for t in ['accounts_user_groups', 'accounts_user_user_permissions', 'accounts_user', 'videos_video', 'videos_subject', 'django_migrations']:
        try: cursor.execute(f'DROP TABLE IF EXISTS {t} CASCADE;')
        except: pass
