# -*- coding: utf-8 -*-
import re


from httplib2 import Http
from .general import get_tree, _get_one_element, to_utf8


class BaseCrawler(object):
    def __init__(self):
        self.ids = []

    def get_ids(self):
        return self.ids

    def parse_ids(self, strategy=None):
        raise NotImplementedError("Should have implemented this")

    def _parser(self):
        raise NotImplementedError("Should have implemented this")

    # def save_callback(self, mongo_db, document_id, new_document=True, strategy='default', elasticsearch=None, autocommit=False):
    #     raise NotImplementedError("Should have implemented this")

    def prepare(self, data):
        # If data can't be parsed by etree, save data in self.data
        try:
            self.tree = get_tree(data)
        except ValueError:
            self.tree = None
            self.data = data

    def _parse_url(self, url):
        http_connection = Http()
        response, content = http_connection.request(url, "GET")
        redirect = re.search(r'<meta.*http-equiv=\"Refresh\".+url=([^ ;]+).*\".*\/>', content)
        if redirect:
            return self._parse_url(redirect.groups()[0])
        return response, content

    def parse_url(self, url):
        response, content = self._parse_url(url)
        self.tree = get_tree(content)
        return response, content

    def parse_document(self, doc_id_or_url):
        parser = self._parser()
        return parser.parse_from_id_or_url(doc_id_or_url)
