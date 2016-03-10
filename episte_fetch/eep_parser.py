# -*- coding: utf-8 -*-
import re
from urlparse import urlparse, parse_qs

from httplib2 import Http

from .general import get_tree, _get_one_element, to_utf8
from .base_parser import BaseParser
from .pubmed_parser import Pubmed


class EvidenciasEnPediatria(BaseParser):
    def __init__(self):
        self.tree = None
        super(EvidenciasEnPediatria, self).__init__()

    def _parse_authors(self):
        authors = self.tree.xpath('//div[@id="autores"]/a/text()')
        return authors

    def _parse_same_as(self):
        return None

    def _parse_doi(self):
        return None

    def _parse_date(self):
        date = [el for el in _get_one_element(self.tree.xpath('//strong[text()="Publication  date: "]/..')).itertext()][-1] or ''
        date = date.split('/')
        date.reverse()
        return '-'.join(date)

    @staticmethod
    def possible_sources():
        return ['evidenciasenpediatria']

    def _parse_source(self):
        return self.possible_sources()[0]

    def _parse_languages(self):
        language_copyright = ''
        self.titles = {}
        self.copyright = {}
        self.titles['en'] = _get_one_element(self.tree.xpath('//h1[@id="titulo_articulo"]/text()'))

        http_connection = Http()
        response, content = http_connection.request(self._get_es_url(), "GET")
        self.es_tree = get_tree(content)
        self.titles['es'] = _get_one_element(self.es_tree.xpath('//h1[@id="titulo_articulo"]/text()'))

        language_abstract = self._parse_language_abstract()
        languages = {}
        for lang in self.titles.keys():
            languages[lang] = {
                'title': self.to_utf8(self.titles[lang]),
                'abstract': self.to_utf8(language_abstract.get(lang)),
                'copyright': language_copyright.strip(),
                'translation_status': 'blocked',
            }
        return languages

    def _parse_language_abstract(self):
        def get_abstract(div):
            abstract = ''
            for child in div.getchildren():
                if len(child.getchildren()):
                    abstract += child.getchildren()[0].text.upper()
                abstext = [text for text in child.itertext()]
                if len(abstext):
                    abstract += abstext[-1] + '\n'
            return abstract
        abstract = {'en': get_abstract(_get_one_element(self.tree.xpath('//div[@id="contenido_resumen"]/div'))).replace('\r', '').strip()}
        if self.es_tree is not None:
            abstract['es'] = get_abstract(_get_one_element(self.es_tree.xpath('//div[@id="contenido_resumen"]/div'))).replace('\r', '').strip()

        return abstract

    def _parse_year(self):
        return self._parse_date()[:4]

    def _parse_publication_type(self):
        publication = _get_one_element(self.tree.xpath('//h2[@id="titulo_revista"]/text()')).split('. ')
        _pub_type = {
            'title': 'Evidencias en pediatría',
            'issue': publication[0],
            'volume': publication[1].split(' ')[-1],
            'number': publication[2].split(' ')[-1],
            'ISSN': '1885-7388',
            'year': self.year,
            'type': 'journal'
        }
        return _pub_type

    def _parse_links(self):
        _links = [{
            'link': _get_one_element(self.tree.xpath('//*[@id="myTabs"]/li/a[contains(@href, ".PDF")]/@href')),
            'name': 'Fulltext link'
        }]
        return _links

    def _parse_eep_id(self):
        return _get_one_element(self.tree.xpath('//input[@name="_idRegistro"]/@value'))

    def _parse_pmid(self):
        pubmed_url = _get_one_element(self.tree.xpath('//*[@id="myTabContent"]//a[contains(@href, "http://www.ncbi.nlm.nih.gov")]/@href'))
        return parse_qs(urlparse(pubmed_url).query).get('from_uid', [''])[0]

    def parse(self, html):
        BaseParser.prepare(self, html)

        document = BaseParser.get_json(self)

        self.validate()

        document['info']['ids']['evidenciasenpediatria'] = self._parse_eep_id()
        document['info']['ids']['infered_pubmed'] = self._parse_pmid()
        document['info']['source'] = self._parse_source()
        document['info']['classification'] = 'structured-summary-of-systematic-review'
        document['info']['links'] = self._parse_links()
        return document

    def parse_from_id_or_url(self, id_or_url):
        url = id_or_url
        if 'http://www.evidenciasenpediatria.es/articulo/' in id_or_url:
            id_or_url = re.search(r'http://www\.evidenciasenpediatria\.es/articulo/([0-9]+)/.*', id_or_url).group(0)
        url_search = re.search(r'http://www\.evidenciasenpediatria\.es/articulo\.php\?lang=(es|en)&id=([0-9]+)', id_or_url)
        if url_search:
            id_or_url = url_search.group(2)
        url = 'http://www.evidenciasenpediatria.es/articulo.php?lang=en&id=%s' % id_or_url
        return self.parse_url(url)

    def _get_es_url(self):
        return 'http://www.evidenciasenpediatria.es/articulo.php?lang=es&id=%s' % self._parse_eep_id()

    @staticmethod
    def get_url_with_id(id_):
        return 'http://www.evidenciasenpediatria.es/articulo.php?lang=en&id=%s' % id_

    @staticmethod
    def is_valid_url(url):
        match = re.search(r'http://www\.evidenciasenpediatria\.es/articulo\.php?lang=(en|es)&id=([0-9]+)', url)
        return match is not None

    # @staticmethod
    # def parse_issue(issue, mongo_db, elasticsearch):
    #     issue_resp, issue_content = Http().request('http://www.evidenciasenpediatria.es/revista/%s' % issue)
    #     issue_tree = get_tree(issue_content)
    #     ids = [link.split('/')[2] for link in issue_tree.xpath('//span[text()="AVC"]/following-sibling::a/@href')]
    #     for eep_id in ids:
    #         parser = EvidenciasEnPediatria()
    #         document = parser.parse_from_id_or_url(eep_id)
    #         parser.save(document, mongo_db, elasticsearch)


class EvidenciasEnPediatriaXML(BaseParser):
    def __init__(self):
        self.tree = None
        super(EvidenciasEnPediatriaXML, self).__init__()

    def _parse_authors(self):
        authors = self.tree.xpath('./authors/author')
        return authors

    def _parse_same_as(self):
        return None

    def _parse_doi(self):
        return None

    def _parse_date(self):
        date = _get_one_element(self.tree.xpath('./pubDate'))
        date = date.split('/')
        date.reverse()
        return '-'.join(date)

    @staticmethod
    def possible_sources():
        return ['evidenciasenpediatria']

    def _parse_source(self):
        return self.possible_sources()[0]

    def _parse_languages(self):
        languages = {
            'es': {
                'title': to_utf8(_get_one_element(self.tree.xpath('./title'))),
                'abstract': to_utf8(_get_one_element(self.tree.xpath('./abstract'))),
                'copyright': '',
                'translation_status': 'blocked',
            }
        }
        return languages

    def _parse_year(self):
        return self._parse_date()[:4]

    def _parse_publication_type(self):
        return {}

    def _parse_eep_id(self):
        url = _get_one_element(self.tree.xpath('./link'))
        eepid = re.search(r'.*DetalleArticulo/(.*)', url).groups()[0]
        return eepid

    def parse(self, html):
        BaseParser.prepare(self, html)

        document = BaseParser.get_json(self)

        self.validate()

        document['info']['ids']['evidenciasenpediatria'] = self._parse_eep_id()
        document['info']['source'] = self._parse_source()
        document['info']['classification'] = 'structured-summary-of-systematic-review'
        return document

    def parse_from_id_or_url(self, id_or_url):
        url = id_or_url
        if 'http://www.evidenciasenpediatria.es/articulo/' in id_or_url:
            id_or_url = re.search(r'http://www\.evidenciasenpediatria\.es/articulo/([0-9]+)/.*', id_or_url).group(0)
        url_search = re.search(r'http://www\.evidenciasenpediatria\.es/articulo\.php\?lang=(es|en)&id=([0-9]+)', id_or_url)
        if url_search:
            id_or_url = url_search.group(2)
        url = 'http://www.evidenciasenpediatria.es/articulo.php?lang=en&id=%s' % id_or_url
        return self.parse_url(url)

    def _get_es_url(self):
        return 'http://www.evidenciasenpediatria.es/articulo.php?lang=es&id=%s' % self._parse_eep_id()

    @staticmethod
    def get_url_with_id(id_):
        return 'http://www.evidenciasenpediatria.es/articulo.php?lang=en&id=%s' % id_

    @staticmethod
    def is_valid_url(url):
        match = re.search(r'http://www\.evidenciasenpediatria\.es/articulo\.php?lang=(en|es)&id=([0-9]+)', url)
        return match is not None

    # @staticmethod
    # def parse_issue(issue, mongo_db, elasticsearch):
    #     issue_resp, issue_content = Http().request('http://www.evidenciasenpediatria.es/revista/%s' % issue)
    #     issue_tree = get_tree(issue_content)
    #     ids = [link.split('/')[2] for link in issue_tree.xpath('//span[text()="AVC"]/following-sibling::a/@href')]
    #     for eep_id in ids:
    #         parser = EvidenciasEnPediatria()
    #         document = parser.parse_from_id_or_url(eep_id)
    #         parser.save(document, mongo_db, elasticsearch)