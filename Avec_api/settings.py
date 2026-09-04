from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)by5(63t9u_+s!@-j41yzybz77m8*of&z2(1=c4v!0cf160n2$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['ceparcrea.acedh-rdc.org', 'www.ceparcrea.acedh-rdc.org', '127.0.0.1', 'localhost']


# -------------------------------------------------------------
# APPLICATION DEFINITION
# -------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'Api_Avec_App',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Doit rester en premier
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Avec_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'Avec_api.wsgi.application'


# -------------------------------------------------------------
# AUTHENTICATION & REST FRAMEWORK
# -------------------------------------------------------------

AUTH_USER_MODEL = 'Api_Avec_App.Utilisateur'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# -------------------------------------------------------------
# CORS CONFIGURATION
# -------------------------------------------------------------


CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://aprepos.vercel.app",
]
CORS_ALLOW_CREDENTIALS = False
SECURE_SSL_REDIRECT = False 
CORS_ALLOW_HEADERS = [
    "content-type",
    "authorization",
    "x-csrftoken",
    "accept",
    "origin",
    "user-agent",
]


# -------------------------------------------------------------
# DATABASE
# -------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'c2798164c_ceparcrea_bd',
        'USER': 'c2798164c_ceparcrea_users',
        'PASSWORD': 'Admin_ceparcea@2026',  
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'CONN_MAX_AGE': 0,                     
        'OPTIONS': {
            'ssl': False,                      
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# -------------------------------------------------------------
# PASSWORD VALIDATION
# -------------------------------------------------------------

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


# -------------------------------------------------------------
# INTERNATIONALIZATION
# -------------------------------------------------------------

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Lubumbashi'
USE_I18N = True
USE_TZ = True


# -------------------------------------------------------------
# STATIC FILES
# -------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'