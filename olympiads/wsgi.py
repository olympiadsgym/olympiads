import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'olympiads.settings')

# Run migrations automatically on cold start (Vercel serverless)
try:
    from django.core.management import call_command
    call_command('migrate', '--noinput', verbosity=0)
except Exception as e:
    print(f"Migration error: {e}")

application = get_wsgi_application()
