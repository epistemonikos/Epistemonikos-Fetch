# -*- coding: utf-8 -*-

# import htmlentitydefs
import re
import inspect
import decorator

from lxml import etree
from lxml.etree import _ElementUnicodeResult

LANGUAGES = {
    'ar': 'العربية',
    'de': 'Deutsch',
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'it': 'Italiano',
    'nl': 'Nederlands',
    'pt': 'Português',
    'zh': '中文'
}

def get_tree(content):
    try:
        parser = etree.XMLParser()
        return etree.fromstring(content, parser)
    except:
        parser = etree.HTMLParser()
        return etree.fromstring(content, parser)

def _get_one_element(elements, default=None):
    return (elements[:1] or [default])[0]

def batch_gen(data, batch_size):
    for i in range(0, len(data), batch_size):
            yield data[i:i+batch_size]

def to_utf8(text):
    if type(text) in (_ElementUnicodeResult, unicode):
        return text.encode('utf-8')
    return text

def date_format(_format):
    def _do_format(func, *args, **kwargs):
        argspec = inspect.getargspec(func)[0]
        for _date in ['mindate', 'maxdate']:
            if _date in argspec:
                _pos = argspec.index(_date)
                args = list(args)
                args[_pos] = _format(args[_pos])
                args = tuple(args)
        return func(*args, **kwargs)
    return decorator.decorator(_do_format)

def date_to_year(date):
    if isinstance(date, int):
        return date
    elif isinstance(date, str):
        _year = re.findall(r'\d{4}', '10/10/2010')
        _year = _year[0] if len(_year) == 1 else date
        return _year
