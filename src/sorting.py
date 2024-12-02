import locale
from collections import namedtuple
from functools import cmp_to_key
from contextlib import contextmanager

LocaleInfo = namedtuple('LocaleInfo', ['strcoll', 'strxfrm'])

@contextmanager
def assume_locale(code, category=locale.LC_COLLATE):
    current = None
    try:
        current = locale.setlocale(category, None)
        locale.setlocale(category, code)
        yield LocaleInfo(strcoll=locale.strcoll, strxfrm=locale.strxfrm)
    finally:
        locale.setlocale(category, current)
