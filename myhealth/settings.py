"""
Django settings for myhealth project.
"""

from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# --- GCP Secret Manager 설정 (Fitbit API용) ---
try:
    from google.cloud import secretmanager

    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'api-test-468900')

    if GCP_PROJECT_ID and GCP_PROJECT_ID != "YOUR_GCP_PROJECT_ID_HERE":
        SECRET_CLIENT = secretmanager.SecretManagerServiceClient()

        def get_secret(secret_id, version_id="latest"):
            name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
            response = SECRET_CLIENT.access_secret_version(name=name)
            return response.payload.data.decode("UTF-8")

        FITBIT_CLIENT_ID = get_secret("fitbit-client-id")
        FITBIT_CLIENT_SECRET = get_secret("fitbit-client-secret")
    else:
        # GCP Secret Manager 사용 안 함 - 환경변수에서 직접 로드
        FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID', '')
        FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET', '')

except Exception as e:
    print(f"Warning: Could not load from GCP Secret Manager: {e}", file=sys.stderr)
    print("Falling back to environment variables...", file=sys.stderr)
    # Fallback to environment variables
    FITBIT_CLIENT_ID = os.getenv('FITBIT_CLIENT_ID', '')
    FITBIT_CLIENT_SECRET = os.getenv('FITBIT_CLIENT_SECRET', '')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['myhealthpartner.app', 'www.myhealthpartner.app', '34.66.237.211', 'localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST Framework
    'rest_framework_simplejwt',  # JWT 인증
    'fitbit',  # 추가된 앱
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myhealth.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # templates 디렉토리 추가
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

WSGI_APPLICATION = 'myhealth.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'frontend/dist',
]

# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Fitbit API 설정
FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_API_BASE_URL = "https://api.fitbit.com"
FITBIT_SCOPE = "activity heartrate location nutrition profile settings sleep social weight oxygen_saturation respiratory_rate temperature cardio_fitness electrocardiogram"

# Session 설정 - DB 기반 세션 사용 (권장)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Django 기본값

# Django Admin 로그인 URL 설정
LOGIN_URL = '/admin/login/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'formatter': 'detailed',
        },
        'polar_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/polar.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'fitbit': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'fitbit.views.polar_views': {
            'handlers': ['polar_file', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Django REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# JWT 설정
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),  # Access Token 유효기간 24시간
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),  # Refresh Token 유효기간 30일
    'ROTATE_REFRESH_TOKENS': True,  # Refresh Token 갱신 시 새로운 Refresh Token 발급
    'BLACKLIST_AFTER_ROTATION': False,  # 기존 Refresh Token을 블랙리스트에 추가하지 않음
    'UPDATE_LAST_LOGIN': True,  # 로그인 시 last_login 업데이트

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}
