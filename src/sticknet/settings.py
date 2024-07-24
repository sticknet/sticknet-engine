import os, requests, socket, sys
from socket import gethostname, gethostbyname
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if 'RDS_DB_NAME' in os.environ:
    DEBUG = False
    PREPEND_WWW = True
    ALLOWED_HOSTS = ['sticknet.org', 'www.sticknet.org', 'www.stiiick.com',
                     'stiiick.com', 'localhost',
                     'sticknet-engine-v02.eu-central-1.elasticbeanstalk.com',
                     'www.sticknet-engine-v02.eu-central-1.elasticbeanstalk.com'
                     '169.254.169.254']
    url = "http://169.254.169.254/latest/meta-data/public-ipv4"
    r = requests.get(url)
    instance_ip = r.text
    ALLOWED_HOSTS += [instance_ip]
    ALLOWED_HOSTS += [gethostbyname(gethostname())]
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
    STATICFILES_LOCATION = 'static'
    STATICFILES_STORAGE = 'custom_storages.StaticStorage'
    PUBLICFILES_LOCATION = 'public'
    PUBLICFILES_STORAGE = 'custom_storages.PublicStorage'
    MEDIAFILES_LOCATION = 'media'
    DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
    MEDIA_PATH = 'https://' + os.environ['CDN'] + '/media/'
    CHAT_MEDIA_PATH = 'https://' + os.environ['STATIC_CDN'] + '/static/'
else:
    DEBUG = True
    env_path = os.path.join(BASE_DIR, '../.env')
    dev_env_path = os.path.join(BASE_DIR, '../.env.dev')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv(dev_env_path)
    ALLOWED_HOSTS = ['*']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'sticknet',
            'USER': 'postgres',
            'PASSWORD': os.environ['LOCAL_DB_PASS'],
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    INTERNAL_IPS = [ip]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    }
    MEDIA_PATH = 'http://' + ip + ':8000/media/'
    CHAT_MEDIA_PATH = 'http://' + ip + ':8000/media/'
    STATICFILES_LOCATION = 'static'
    MEDIAFILES_LOCATION = 'media'
    PUBLICFILES_LOCATION = 'public'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

TESTING = sys.argv[1:2] == ['test'] or 'DEV' in os.environ
if not TESTING:
    CRED = credentials.Certificate(os.environ['FIREBASE_CREDENTIALS'])
DEFAULT_APP = firebase_admin.initialize_app(CRED) if not TESTING else None

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
PROJECT_APPS = [
    'chat',
    'groups',
    'notifications',
    'photos',
    'support',
    'users',
    'stick_protocol',
    'keys',
    'iap',
    'vault'
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'knox',
    'webpack_loader',
    'storages',
    'django_cleanup.apps.CleanupConfig',
    'django_otp',
    'django_otp.plugins.otp_totp',
]
# if DEBUG:
#     THIRD_PARTY_APPS.append('debug_toolbar')


INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_PORT = 587

ADMINS = [('Admin', os.environ['ERRORS_EMAIL'])]

WEBPACK_LOADER = {
    'DEFAULT': {
        'CACHE': not DEBUG,
        'BUNDLE_DIR_NAME': 'bundles/',  # must end with slash
        'STATS_FILE': os.path.join(BASE_DIR, '../webpack/webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
    }
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AWS_S3_OBJECT_PARAMETERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'CacheControl': 'max-age=94608000',
}
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_STATIC_BUCKET_NAME = os.environ['AWS_STATIC_BUCKET_NAME']
AWS_PUBLIC_BUCKET_NAME = os.environ['AWS_PUBLIC_BUCKET_NAME']

AWS_S3_REGION_NAME = os.environ['AWS_S3_REGION_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

STORJ_BUCKET_NAME = os.environ['STORJ_DEV_BUCKET_NAME'] if DEBUG else os.environ['STORJ_BUCKET_NAME']

# AWS_CLOUDFRONT_KEY = os.environ['AWS_CLOUDFRONT_KEY']
# AWS_CLOUDFRONT_KEY_ID = os.environ['AWS_CLOUDFRONT_KEY_ID']
# AWS_S3_CUSTOM_DOMAIN = os.environ['CDN']

# with open(os.environ['AWS_CLOUDFRONT_KEY'], 'rb') as sk:
#     data = sk.read()
# AWS_CLOUDFRONT_KEY = data
# AWS_CLOUDFRONT_KEY_ID = os.environ['AWS_CLOUDFRONT_KEY_ID']


# AWS_CLOUDFRONT_KEY = os.environ['AWS_CLOUDFRONT_KEY'].encode('ascii')
# AWS_CLOUDFRONT_KEY_ID = os.environ['AWS_CLOUDFRONT_KEY_ID']
# AWS_DEFAULT_ACL = None
# AWS_S3_FILE_OVERWRITE = False


# Tell django-storages the domain to use to refer to static files.
# AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
# AWS_IS_GZIPPED = True
# GZIP_CONTENT_TYPES = ('application/json', 'image/jpeg', 'text/css', 'text/javascript', 'application/javascript',
#                       'application/x-javascript', 'image/svg+xml')

# Tell the staticfiles app to use S3Boto3 storage when writing the collected static files (when
# you run `collectstatic`).
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
}

REST_KNOX = {
    'TOKEN_TTL': None
}

DATA_UPLOAD_MAX_MEMORY_SIZE = None

AUTH_USER_MODEL = 'users.User'
GROUP_MODEL = 'groups.Group'

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)

if DEBUG:
    MIDDLEWARE = []
    # MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware']
else:
    MIDDLEWARE = []
MIDDLEWARE += [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_otp.middleware.OTPMiddleware',
]

ROOT_URLCONF = 'sticknet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

# 'awseb-awseb-7hh5hgmxregl-955074069.eu-central-1.elb.amazonaws.com',
# 'ec2-3-124-226-193.eu-central-1.compute.amazonaws.com',
# FIREBASE_REF = 'https://stiiick-1545628981656.firebaseio.com/'
FIREBASE_REF = 'https://sticknet.firebaseio.com/'
FIREBASE_REF_DEV = 'https://stiiick-dev.firebaseio.com/'

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/


# STATICFILES_DIRS = [
#     # will not be served, long term storage
#     os.path.join(BASE_DIR, "static-storage"),
# ]


STATIC_ROOT = os.path.join(BASE_DIR, "..", "www", "static")
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, '../webpack/assets'),
)

MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')
MEDIA_URL = '/media/'

PUBLIC_ROOT = os.path.join(BASE_DIR, '..', 'public')
PUBLIC_URL = '/public/'

WSGI_APPLICATION = 'sticknet.wsgi.application'
