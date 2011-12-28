import os
import sys
import site

PROJECT_ROOT = os.path.abspath(os.path.split(__file__)[0])
site_packages = os.path.join(PROJECT_ROOT, 'backtoshops-env/lib/python2.7/site-packages')
site.addsitedir(site_packages)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'backtoshops'))
sys.path.insert(0, PROJECT_ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] = 'backtoshops.settings_production'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
