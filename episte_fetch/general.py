# -*- coding: utf-8 -*-
from lxml import etree
from lxml.etree import _ElementUnicodeResult



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