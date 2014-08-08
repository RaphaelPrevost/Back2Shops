import tenjin
tenjin.set_template_encoding('utf-8')
from tenjin.helpers import *

import settings
from common.m17n import trans_func

global temp_engine
temp_engine = None

def get_engine(force=False, **kwargs):
    global temp_engine
    if temp_engine is not None and not force:
        return temp_engine
    temp_engine = tenjin.Engine(preprocess=True,
                                path=settings.TEMPLATE_PATH,
                                **kwargs)
    return temp_engine

def render_template(template, content, **kwargs):
    content['_'] = trans_func
    return get_engine(**kwargs).render(template, content)

