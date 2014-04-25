import tenjin
from tenjin.helpers import *

import settings

global temp_engine
temp_engine = None

def get_engine(force=False, **kwargs):
    global temp_engine
    if temp_engine is not None and not force:
        return temp_engine

    temp_engine = tenjin.Engine(path=settings.TEMPLATE_PATH,
                                layout=settings.DEFAULT_TEMPLATE,
                                **kwargs)
    return temp_engine

def render_template(template, content, **kwargs):
    return get_engine(**kwargs).render(template, content)
