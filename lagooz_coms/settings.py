import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*gc93%lm!v&udq%yt$bj-&c0$(2cr^e)gj1hsg+zq7w-8=nyhk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


AUTH_USER_MODEL = 'accounts.CustomUser'  # Update this to point to your custom user model

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap4',
]


CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap4"]
CRISPY_TEMPLATE_PACK = "bootstrap4"



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lagooz_coms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lagooz_coms.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'coms_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'; SET NAMES utf8mb4 COLLATE utf8mb4_general_ci;",
        },
        'TEST': {
            'NAME': 'lagooz_coms_db_test',
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

# LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'

# USE_I18N = True

# USE_TZ = True




LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Lagos' 

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/


# URL to use when referring to static files

# # Static files (CSS, JavaScript, images)
# STATIC_URL = '/static/'

# # If you're deploying to production, specify the location for static files
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),  # Default static folder
# ]


STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# This is where static files will be collected into during deployment
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Only needed in production

# Serve static files through a CDN or directly from a web server like Nginx in production
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'  # For custom storage backends


# # Media files (uploads from users)
# MEDIA_URL = '/media/'  # The URL where media files will be accessible

# # The file system path to store uploaded files
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # The directory where user-uploaded files will be stored

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


LOGIN_URL = 'login'  # This assumes the 'login' URL name exists



from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-due-communications-every-minute': {
        'task': 'communications.tasks.send_due_communications',  # path to your task
        'schedule': crontab(minute='*/1'),  # every minute
    },
}



CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'


# # settings.py
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your_email@example.com'
# EMAIL_HOST_PASSWORD = 'your_password'
# DEFAULT_FROM_EMAIL = 'Your App Name <noreply@example.com>'
