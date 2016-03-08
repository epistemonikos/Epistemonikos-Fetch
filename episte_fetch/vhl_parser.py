# -*- coding: utf-8 -*-
import HTMLParser
import re
from urlparse import urlparse

from xml.etree import ElementTree

from httplib2 import Http
from .base_parser import BaseParser
from .general import get_tree, to_utf8, LANGUAGES


class VHL(BaseParser):
    def __init__(self):
        self.tree = None
        super(VHL, self).__init__()
        self.ids = {}

    def _parse_authors(self):
        return self.tree.xpath('./*[@name="au"]/str/text()')

    def _parse_vhl_id(self):
        self.ids['vhl'] = self.tree.xpath('./*[@name="id"]/text()')[0]
        return self.ids['vhl']

    def _parse_same_as(self):
        return "http://search.bvsalud.org/portal/resource/en/%s" % self._parse_vhl_id()

    def _parse_doi(self):
        return None

    def _parse_date(self):
        date = self.tree.xpath('./*[@name="entry_date"]/text()')
        if date:
            return date[0].replace('-', '/')

    @staticmethod
    def possible_sources():
        return ['LILACS', 'VHL']

    def _parse_source(self):
        return (self.tree.xpath('./*[@name="db"]/str/text()') or ['VHL'])[0]

    def _parse_languages(self):
        parser = HTMLParser.HTMLParser()
        languages = {}
        for key in LANGUAGES.keys():
            title = self.tree.xpath('./*[@name="ti_%s"]/str/text()' % key)
            if title:
                abstract = self.tree.xpath('./*[@name="ab_%s"]/str/text()' % key)
                abstract = parser.unescape(abstract[0]) if abstract else ''
                languages[key] = {
                    'title': to_utf8(title[0]),
                    'abstract': to_utf8(abstract),
                    'copyright': ''
                }
        return languages

    def _parse_year(self):
        if self.date:
            return self.date.split('/')[0]

    def _parse_links(self):
        links = self.tree.xpath('./*[@name="ur"]/str/text()')
        return [{'name': urlparse(link).hostname, 'link': link} for link in links]

    @staticmethod
    def _country_format(text):
        not_changed = ['and', 'of', 'the', 'former', 'part']
        if text:
            words = text.split(' ')
            words = [word if word in not_changed else word.capitalize() for word in words]
            return ' '.join(words)
        return text

    def _parse_country(self, document, mongo_db, elasticsearch=None):
        countries = self.tree.xpath('.//*[@name="pais_afiliacao"]/str/text()')
        if countries:
            for country in countries:
                country_match = re.search(r'\^i([^\^]*)', countries[0])
                if country_match:
                    document.save_metadata(
                        mongo_db=mongo_db,
                        tag='country',
                        value=self._country_format(country_match.group(1)),
                        elasticsearch=elasticsearch
                    )

    def prepare_multiple(self, data):
        _tree = get_tree(data.replace('xmlns="http://www.w3.org/1999/xhtml"', ''))

        for _doc in _tree.xpath('//result/doc'):
            self.tree = _doc
            self.parse_fields()
            yield

    def parse_multiple(self, xml):
        documents_json = []
        try:
            xml = xml.decode('utf-8')
        except Exception:
            pass

        for _doc in self.prepare_multiple(xml.encode('utf-8')):

            status, msg = self.validate()
            if not status:
                document_json = {'error': msg}
            else:
                document_json = self.get_json()
                for key, value in self.ids.iteritems():
                    document_json['info']['ids'][key] = value
                document_json['info']['links'] = self._parse_links()
            documents_json.append(document_json)

        return documents_json

    def parse(self, xml):
        try:
            xml = xml.decode('utf-8')
        except Exception:
            pass
        BaseParser.prepare(self, xml.encode('utf-8'))
        self.validate()
        document_json = self.get_json()
        for key, value in self.ids.iteritems():
            document_json['info']['ids'][key] = value
        document_json['info']['links'] = self._parse_links()
        return document_json

    @staticmethod
    def _get_document_xml(source_id):
        http = Http()
        url = 'http://search.bvsalud.org/portal/?output=xml&lang=en&page=1&q=id:"%s"' % source_id
        response, content = http.request(url)
        try:
            content = content.decode('utf-8')
        except Exception:
            pass
        content = content.encode('utf-8')
        tree = get_tree(content)
        document_xml_element = tree.xpath('.//doc')[0]
        return ElementTree.tostring(document_xml_element, 'utf-8')

    def parse_from_id_or_url(self, id_or_url):
        if len(id_or_url.split('/')) >= 2:  # Is an URL
            ids = re.match("http://search.bvsalud.org/portal/resource/en/(.*)", id_or_url)
            if ids:
                id_or_url = ids.group(1)
        return self.parse(self._get_document_xml(id_or_url))

    def parse_url(self, url):
        return self.parse_from_id_or_url(url)

    def _parse_publication_type(self):
        title = self.tree.xpath('./*[@name="ta"]/str/text()')
        if title:
            publication_type = {
                'type': 'journal',
                'year': self.year,
                'title': title[0]
            }
            issue = self.tree.xpath('./*[@name="ip"]/str/text()')
            if issue:
                publication_type['issue'] = issue[0]
            volume = self.tree.xpath('./*[@name="vi"]/str/text()')
            if volume:
                publication_type['volume'] = volume[0]
            pagination = self.tree.xpath('./*[@name="pg"]/str/text()')
            if pagination:
                publication_type['pagination'] = pagination[0]
            return publication_type

    # def is_valid_url(self, url):
    #     if url:
    #         return 'http://search.bvsalud.org/portal/resource/en/' in url
    #     return False

