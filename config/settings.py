import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# A virtualenv on PythonAnywhere lives under /home/<username>/.
PA_DOMAIN = os.environ.get('PYTHONANYWHERE_DOMAIN', '').strip()
ON_PYTHONANYWHERE = bool(PA_DOMAIN) or sys.prefix.startswith('/home/')


def _env_flag(name, default):
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'ir-maintenance-demo-key-change-before-any-public-deploy',
)
# Local demo stays in debug mode. The hosted site turns debug off automatically.
DEBUG = _env_flag('DJANGO_DEBUG', default=not ON_PYTHONANYWHERE)

if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS = [host.strip() for host in os.environ['ALLOWED_HOSTS'].split(',') if host.strip()]
elif ON_PYTHONANYWHERE:
    ALLOWED_HOSTS = [host for host in (PA_DOMAIN, '.pythonanywhere.com') if host]
else:
    ALLOWED_HOSTS = ['*']

if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS = [
        origin.strip() for origin in os.environ['CSRF_TRUSTED_ORIGINS'].split(',') if origin.strip()
    ]
elif ON_PYTHONANYWHERE:
    CSRF_TRUSTED_ORIGINS = ['https://*.pythonanywhere.com']
    if PA_DOMAIN:
        CSRF_TRUSTED_ORIGINS.insert(0, f'https://{PA_DOMAIN}')

if ON_PYTHONANYWHERE:
    # The site is HTTPS at the browser; PythonAnywhere talks to Django over HTTP.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'maintenance.apps.MaintenanceConfig',
]

try:
    import whitenoise  # noqa: F401
    _USE_WHITENOISE = True
except ImportError:
    _USE_WHITENOISE = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]
if _USE_WHITENOISE:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
MIDDLEWARE += [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'maintenance.middleware.ActiveUserMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'maintenance.context_processors.nav',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
]

AUTH_USER_MODEL = 'maintenance.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_500_000
DATA_UPLOAD_MAX_MEMORY_SIZE = 350 * 1024 * 1024
