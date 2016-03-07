# -*- coding: utf-8 -*-
import re

from httplib2 import Http
from .general import get_tree, to_utf8, _get_one_element

class BaseParser(object):

    ERRORS = {
        'no_lang': 'Languages not parsed',
        'inc_lang': 'Languages incomplete'
    }

    def __init__(self):
        self.authors = []
        self.same_as = None
        self.doi = None
        self.date = None
        self.source = None
        self.languages = {}
        self.year = None
        self.copyright = None
        self.publication_type = None

    def _parse_authors(self):
        raise NotImplementedError("Should have implemented this")

    def _parse_same_as(self):
        raise NotImplementedError("Should have implemented this")

    def _parse_doi(self):
        raise NotImplementedError("Should have implemented this")

    def _parse_date(self):
        raise NotImplementedError("Should have implemented this")

    def _parse_source(self):
        raise NotImplementedError("Should have implemented this")

    def _parse_languages(self):
        raise NotImplementedError("Should have implemented this")

    def _parse_year(self):
        raise NotImplementedError("Should have implemented this")

    def parse(self):
        raise NotImplementedError("Should have implemented this")

    def parse_from_id_or_url(self, id_or_url):
        raise NotImplementedError("Should have implemented this")

    def _parse_publication_type(self):
        raise NotImplementedError("Should have implemented this")

    def prepare(self, data):
        # If data can't be parsed by etree, save data in self.data
        try:
            self.tree = get_tree(data.replace('xmlns="http://www.w3.org/1999/xhtml"', ''))
        except Exception:
            self.tree = None
            self.data = data
        self.parse_fields()

    def parse_fields(self):
        self.authors = self._parse_authors()
        self.doi = self._parse_doi()
        self.date = self._parse_date()
        self.source = self._parse_source()
        self.languages = self._parse_languages()
        self.year = self._parse_year()
        self.same_as = self._parse_same_as()
        self.publication_type = self._parse_publication_type()

    def get_json(self):
        document_json = {}
        document_json['info'] = {}
        document_json['info']['author'] = map(to_utf8, self.authors)
        document_json['info']['ids'] = {'doi': to_utf8(self.doi)}
        document_json['info']['date'] = to_utf8(self.date)
        document_json['info']['source'] = to_utf8(self.source)
        document_json['languages'] = self.languages
        document_json['info']['year'] = to_utf8(self.year)
        document_json['info']['publication_type'] = self.publication_type
        return document_json

    def _parse_url(self, url):
        http_connection = Http()
        response, content = http_connection.request(url, "GET")
        redirect = re.search(r'<meta.*http-equiv=\"Refresh\".+url=([^ ;]+).*\".*\/>', content)
        if redirect:
            return self._parse_url(redirect.groups()[0])
        return response, content

    def parse_url(self, url):
        response, content = self._parse_url(url)
        return self.parse(content)

    def validate(self):
        lang_keys = self.languages.keys()
        if len(lang_keys) < 1:
            return False, BaseParser.ERRORS['no_lang']
        elif not self.languages[lang_keys[0]]['abstract'] and not self.languages[lang_keys[0]]['title']:
            return False, BaseParser.ERRORS['inc_lang']
        return True, "ok"
