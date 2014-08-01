import logging
import re
import string
from unidecode import unidecode

def normalize_name(name):
    name = name.decode('UTF-8')

    def strict_char(c):
        # keep Chinese
        if u'\u4e00' <= c <= u'\u9fff':
            return c
        try:
            # remove accents and decompose composition
            c = unidecode(c)
            c = ''.join(i for i in c
                        if i in string.ascii_letters or i in string.digits)
            return c.lower()
        except Exception, e:
            logging.warning("Can not normalize the character '%s' for format "
                            "url of name '%s'", c, name)
            return ''

    str_list = re.split(r' |-', name)
    str_list = map(lambda word: ''.join(map(strict_char, word)), str_list)
    str_list = filter(lambda x: x, str_list) or ['default', ]
    return '-'.join(str_list)
