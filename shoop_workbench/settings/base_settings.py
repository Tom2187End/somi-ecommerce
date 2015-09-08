# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from shoop.addons import add_enabled_addons
import os


BASE_DIR = os.getenv("SHOOP_WORKBENCH_BASE_DIR") or (
    os.path.dirname(os.path.dirname(__file__)))
SECRET_KEY = "Shhhhh"
DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = []

MEDIA_ROOT = os.path.join(BASE_DIR, "var", "media")
STATIC_ROOT = os.path.join(BASE_DIR, "var", "static")
MEDIA_URL = "/media/"

SHOOP_ENABLED_ADDONS_FILE = os.getenv("SHOOP_ENABLED_ADDONS_FILE") or (
    os.path.join(BASE_DIR, "var", "enabled_addons"))
INSTALLED_APPS = add_enabled_addons(SHOOP_ENABLED_ADDONS_FILE, (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_jinja',
    'filer',
    'easy_thumbnails',
    'shoop.core',
    'shoop.simple_supplier',
    'shoop.default_tax',
    'shoop.front',
    'shoop.front.apps.registration',
    'registration',
    'shoop.front.apps.auth',
    'shoop.front.apps.customer_information',
    'shoop.front.apps.personal_order_history',
    'shoop.front.apps.simple_order_notification',
    'shoop.front.apps.simple_search',
    'shoop.admin',
    'shoop.addons',
    'shoop.testing',
    'bootstrap3',
    'shoop.notify',
    'shoop.simple_cms',
    'rest_framework',
    'shoop.api',
    'shoop.xtheme',
    'shoop.simple_pricing'
))

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'shoop.front.middleware.ProblemMiddleware',
    'shoop.front.middleware.ShoopFrontMiddleware',

)

ROOT_URLCONF = 'shoop_workbench.urls'
WSGI_APPLICATION = 'shoop_workbench.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
STATIC_URL = '/static/'
LOGIN_REDIRECT_URL = '/'
SOUTH_TESTS_MIGRATE = False  # Makes tests that much faster.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {'format': '[%(asctime)s] (%(name)s:%(levelname)s): %(message)s'},
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'shoop': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
    }
}

LANGUAGES = [
    ('en', 'English'),
    ('fi', 'Finnish'),
    ('ja', 'Japanese'),
]

PARLER_DEFAULT_LANGUAGE_CODE = "en"

PARLER_LANGUAGES = {
    None: [{"code": c, "name": n} for (c, n) in LANGUAGES],
    'default': {
        'hide_untranslated': False,
    }
}

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages"
)

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "context_processors": TEMPLATE_CONTEXT_PROCESSORS,
            "newstyle_gettext": True,
            "environment": "shoop.xtheme.engine.XthemeEnvironment"
        },
        "NAME": "jinja2",
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": TEMPLATE_CONTEXT_PROCESSORS,
            "debug": True
        }
    },
]


SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

SHOOP_PRICING_MODULE = "default_pricing"

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    )
}

if os.environ.get("SHOOP_WORKBENCH_DISABLE_MIGRATIONS") == "1":
    from .utils import DisableMigrations
    MIGRATION_MODULES = DisableMigrations()


def configure(setup):
    setup.commit(globals())
