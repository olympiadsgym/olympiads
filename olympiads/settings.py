from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-me')

# AES-256 key for encrypting Member email and contact in the database.
# Generate: python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default='')


def parse_debug(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on', 'debug', 'development'}


DEBUG = config('DEBUG', default=False, cast=parse_debug)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
ALLOWED_HOSTS += ['.vercel.app', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'members',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.SessionExpireMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'olympiads.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'olympiads.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600,
    )
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email — Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='').strip()
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='').replace(' ', '')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
ADMIN_ALERT_EMAIL = config('ADMIN_ALERT_EMAIL', default='').strip()

# Vercel Cron webhook secret — must match the value set in the Vercel dashboard.
# Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
CRON_SECRET = config('CRON_SECRET', default='')

# Scheduler — daily task run time (UTC, 24-hour format).
DAILY_TASK_HOUR = config('DAILY_TASK_HOUR', default=22, cast=int)
DAILY_TASK_MINUTE = config('DAILY_TASK_MINUTE', default=0, cast=int)

# Session — 30 minute idle timeout
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True

# Security — enforced in production
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://*.vercel.app',
    'https://olympiads-beta.vercel.app',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'