import settings
from django import template

register = template.Library()

@register.simple_tag
@register.filter
def get_lang_iso(lang):
    map = settings.LANG_MAP
    if map.get(lang):
        return map[lang]['iso']
    else:
        r = lang.split('-')
        if len(r) == 2:
            return r[-1]
    return ''

