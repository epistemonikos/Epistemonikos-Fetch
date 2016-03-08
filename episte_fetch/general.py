# -*- coding: utf-8 -*-
# import htmlentitydefs
# import re

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


# def unescape(text):
#     def fixup(m):
#         text = m.group(0)
#         if text[:2] == "&#":
#             # character reference
#             try:
#                 if text[:3] == "&#x":
#                     return unichr(int(text[3:-1], 16))
#                 else:
#                     return unichr(int(text[2:-1]))
#             except ValueError:
#                 pass
#         else:
#             # named entity
#             try:
#                 text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
#             except KeyError:
#                 pass
#         return text  # leave as is
#     return re.sub(r"&#?\w+;", fixup, text)
