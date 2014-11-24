import settings
import gettext as _gettext
from gevent.local import local


translators = {}
_stash = local()

def init_translators():
    domain = settings.LOCALE_DOMAIN
    localedir = settings.LOCALE_DIR
    for locale in settings.SUPPORTED_LOCALES:
        translators[locale] = _gettext.translation(domain, localedir,
                                                  [locale], fallback=True)

def gettext_func(locale=None):
    locale = locale or get_locale()
    translator = translators.get(locale) or _gettext.NullTranslations()
    return translator.gettext

def gettext(msg):
    if msg:
        return gettext_func()(msg)
    return msg


def get_locale():
    try:
        return _stash.user_locale
    except AttributeError:
        return settings.DEFAULT_LOCALE

def set_locale(locale=settings.DEFAULT_LOCALE):
    _stash.user_locale = locale

