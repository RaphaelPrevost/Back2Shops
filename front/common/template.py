import tenjin
tenjin.set_template_encoding('utf-8')
from tenjin.helpers import *

import settings
import urllib
from common.m17n import gettext_func

global temp_engines
temp_engines = {}

def get_engine(force=False, **kwargs):
    global temp_engines
    key = urllib.urlencode(kwargs)
    if temp_engines.get(key) and not force:
        return temp_engines[key]

    engine = tenjin.Engine(preprocess=True,
                           path=settings.TEMPLATE_PATH,
                           **kwargs)
    temp_engines[key] = engine
    return engine

def render_template(template, content, **kwargs):
    if kwargs.get('lang'):
        content['_'] = gettext_func(locale=kwargs['lang'])
    return get_engine(**kwargs).render(template, content)

