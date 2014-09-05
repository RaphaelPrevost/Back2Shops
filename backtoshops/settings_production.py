# Django settings for backtoshops project.
import os

SITE_ROOT = "/home/backtoshops/public_html"
SITE_NAME = ""

get_site_prefix = lambda : '' if SITE_NAME != '' and SITE_NAME is not None else ''

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# this is for pagination
CHOICE_PAGE_SIZE = (10, 20, 50, 100)
DEFAULT_PAGE_SIZE = 10
PAGE_NAV_SIZE = 10

get_page_size = lambda request: int(request.session.get('page_size',DEFAULT_PAGE_SIZE))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'backtoshops',                      # Or path to database file if using sqlite3.
        'USER': 'bts',                      # Not used with sqlite3.
        'PASSWORD': 'backtoshops',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

ugettext = lambda s: s
LANGUAGES = (
    ('en-us', ugettext('English')),
    ('fr-FR', ugettext('French')),
    ('zh-CN', ugettext('Chinese')),
)
LANGUAGES_2 = tuple([(lang[:2], text) for lang, text in LANGUAGES])
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/site_media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'static'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%z^ka7o)y5#gxtr((^a4pnvllhumneehjsc)$c3%+r!%@$i%ua'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'aloha_editor.middleware.AlohaEditorMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    SITE_ROOT+'/backend/templates',
    SITE_ROOT+'/sale/templates',
    SITE_ROOT+'/shop/templates',
    SITE_ROOT+'/accounts/templates',
    SITE_ROOT+'/orders/templates',
    SITE_ROOT+'/routes/templates',
    SITE_ROOT+'/templates',

)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
)

INSTALLED_APPS = (
    'aloha_editor',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    get_site_prefix()+'accounts',
    get_site_prefix()+'address',
    get_site_prefix()+'pictures',
    get_site_prefix()+'shippings',
    get_site_prefix()+'shops',
    get_site_prefix()+'sales',
    get_site_prefix()+'attributes',
    get_site_prefix()+'stocks',
    get_site_prefix()+'backend',
    get_site_prefix()+'fouillis',
    get_site_prefix()+'webservice',
    get_site_prefix()+'barcodes',
    get_site_prefix()+'globalsettings',
    get_site_prefix()+'brandsettings',
    get_site_prefix()+'brandings',
    get_site_prefix()+'countries',
    get_site_prefix()+'emails',
    get_site_prefix()+'orders',
    get_site_prefix()+'taxes',
    get_site_prefix()+'promotion',
    get_site_prefix()+'routes',
    'south',
    'form_utils',
    'formwizard',
    'sorl.thumbnail',
    'django_extensions',
    'formwizard',
    'rosetta',
    'misc',
    'multiwidgetlayout',
)

AUTH_PROFILE_MODULE='accounts.UserProfile'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt': '%a, %d %b %Y %H:%M:%S %z',
        }
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'log_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(SITE_ROOT, '../logs/error.log'),
            'mode': 'a'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': [],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'level': 'ERROR',
            'handlers': ['console', 'log_file'],
            'propagate': True
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    },
    'rosetta': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'ROSETTA_',
    },
}

# debug-toolbar setting:
#INTERNAL_IPS = ('127.0.0.1',)

# sorl-thumbnail setting:
THUMBNAIL_DEBUG = True


# geocoding
GEONAMES_USERNAME = "moonstrap"

# TODO: change according with product env.
USR_SERVER = 'http://92.222.30.2'
FIN_SERVER = 'http://92.222.30.3'
AST_SERVER = 'http://92.222.30.4'
ASSETS_CDN = 'http://92.222.30.4'

SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_SERVER, 'webservice/1.0/pub/apikey.pem'),
    'FIN': os.path.join(FIN_SERVER, 'webservice/1.0/pub/apikey.pem'),
    'AST': os.path.join(AST_SERVER, 'webservice/1.0/pub/apikey.pem'),
}

PRIVATE_KEY_PATH = '/home/backtoshops/public_html/static/keys/adm_pri.key'
PUB_KEY_PATH = '/home/backtoshops/public_html/static/keys/adm_pub.key'

CACHE_INVALIDATION_URL = "%s/webservice/protected/invalidate" % USR_SERVER
SHIPPING_FEE_URL = "%s/webservice/protected/shipping/fee" % USR_SERVER

ORDER_LIST_URL = '%s/webservice/1.0/private/order/orders' % USR_SERVER
ORDER_DETAIL_URL = '%s/webservice/1.0/private/order/detail' % USR_SERVER
ORDER_SHIPPING_LIST = '%s/webservice/1.0/protected/shipping/list' % USR_SERVER
ORDER_SHIPMENT = '%s/webservice/1.0/protected/shipment' % USR_SERVER
ORDER_INVOICES = '%s/webservice/1.0/private/invoice/get' % USR_SERVER
ORDER_SEND_INVOICES = '%s/webservice/1.0/private/invoice/send' % USR_SERVER
ORDER_DELETE = '%s/webservice/1.0/private/order/delete' % USR_SERVER

# config to see decrypt content for response,
# only used for debugging
CRYPTO_RESP_DEBUGING = False


SALE_IMG_UPLOAD_MAX_SIZE = 1024 * 1024  # Bytes, 1M
