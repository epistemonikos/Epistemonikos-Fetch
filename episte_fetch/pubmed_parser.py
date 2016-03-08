# -*- coding: utf-8 -*-
import HTMLParser
import re

from httplib2 import Http

from episte_libs import get_month_number_from_month_text, format_day_text
from .base_parser import BaseParser
from .general import get_tree, to_utf8, _get_one_element

class Pubmed(BaseParser):
    def __init__(self):
        self.tree = None
        super(Pubmed, self).__init__()
        self.ids = {}

    def _parse_authors(self):
        authors_parent_tag = 'Book' if self.is_book else 'MedlineCitation'
        authors = []
        for author in self.tree.xpath('.//%s//AuthorList/Author' % authors_parent_tag):
            last_name = _get_one_element(author.xpath('./LastName/text()'))
            initials_name = _get_one_element(author.xpath('./Initials/text()'))
            collective_name = _get_one_element(author.xpath('./CollectiveName/text()'))
            if initials_name or last_name:
                authors.append(to_utf8("%s %s" % (last_name, initials_name)))
            elif collective_name:
                authors.append(to_utf8(collective_name))
        return authors

    def _parse_doi(self):
        tag_name = 'PubmedBookData' if self.is_book else 'PubmedData'
        return _get_one_element(self.tree.xpath('.//%s//*[@IdType="doi"]/text()' % tag_name))

    def _parse_same_as(self):
        self._parse_ids()
        if self.ids.get('pubmed'):
            return "http://www.ncbi.nlm.nih.gov/pubmed/"+self.ids['pubmed']

    def _parse_cochrane_id(self):
        return _get_one_element(self.tree.xpath(
            './/PubmedArticle/MedlineCitation/Article/Pagination/MedlinePgn/text()'
        ))

    def _parse_clinical_trial_id(self):
        data_bank_name = _get_one_element(self.tree.xpath('.//Article/DataBankList/DataBank/DataBankName/text()'))
        if not data_bank_name or 'ClinicalTrials' not in data_bank_name:
            return None
        nct_id = _get_one_element(self.tree.xpath('.//Article/DataBankList/DataBank/AccessionNumberList/AccessionNumber/text()'))
        return nct_id

    def _parse_ids(self):
        tag_name = 'PubmedBookData' if self.is_book else 'PubmedData'
        valids_ids = ['doi', 'pubmed', 'pii', 'pmc', 'mid']
        for article_id in self.tree.xpath('.//%s/ArticleIdList/ArticleId' % tag_name):
            id_type = article_id.get('IdType')
            if id_type in valids_ids:
                self.ids[id_type] = article_id.text

        # Clinical Trial
        cnt = self._parse_clinical_trial_id()
        if cnt:
            self.ids['clinical_trial_id'] = cnt

        # Cochrane
        cochrane_id = self._parse_cochrane_id()
        if cochrane_id is not None and 'CD' in cochrane_id:
            self.ids['cochrane'] = cochrane_id
        elif self.ids.get('doi'):
            doi_match = re.search("(CD[0-9]+)", self.ids.get('doi'))
            if doi_match:
                self.ids['cochrane'] = doi_match.group(1)

        return self.ids

    def _parse_publication_type(self):
        if self.is_book:
            journals_xpath = {
                'year': './/Book/PubDate/Year/text()',
                'title': './/Book/CollectionTitle/text()',
                'cited_medium': './/Book/Medium/text()',
            }
            publication_type = {'type': 'book'}
        else:
            journals_xpath = {
                'ISSN': './/Journal/ISSN/text()',
                'issue': './/Journal/JournalIssue/Issue/text()',
                'year': './/Journal/JournalIssue/PubDate/Year/text()',
                'title': './/Journal/Title/text()',
                'cited_medium': './/Journal/JournalIssue/@CitedMedium',
                'volume': './/Journal/JournalIssue/Volume/text()',
                'pagination': './/Article/Pagination/MedlinePgn/text()',
            }
            publication_type = {'type': 'journal'}
        for key, value in journals_xpath.iteritems():
            publication_type[key] = to_utf8(_get_one_element(self.tree.xpath(value)))
            if not publication_type[key]:
                del publication_type[key]
        return publication_type

    def _parse_date(self):
        year = _get_one_element(self.tree.xpath('.//Journal/JournalIssue/PubDate/Year/text()'))
        if not year:
            year = _get_one_element(self.tree.xpath('.//Journal/JournalIssue/PubDate/MedlineDate/text()'))
            if year:
                year = re.search(r"(\d{4})", year).groups()[0]


        self.year = year or \
            _get_one_element(self.tree.xpath('.//Book/PubDate/Year/text()'))
        month = _get_one_element(self.tree.xpath('.//Journal/JournalIssue/PubDate/Month/text()')) or \
            _get_one_element(self.tree.xpath('.//Book/PubDate/Month/text()')) or \
            _get_one_element(self.tree.xpath('.//ArticleDate[@DateType="Electronic"]/Month/text()')) or \
            _get_one_element(self.tree.xpath('.//MedlineCitation/DateCreated/Month/text()'))
        day = _get_one_element(self.tree.xpath('.//Journal/JournalIssue/PubDate/Day/text()')) or \
            _get_one_element(self.tree.xpath('.//ArticleDate[@DateType="Electronic"]/Day/text()')) or \
            _get_one_element(self.tree.xpath('.//MedlineCitation/DateCreated/Day/text()'))
        return "%s/%s/%s" % (self.year, get_month_number_from_month_text(month), format_day_text(day))

    @staticmethod
    def possible_sources():
        return ['PubMed', 'ACP']

    def _parse_source(self):
        return self.possible_sources()[0]

    def _parse_languages(self):
        parser = HTMLParser.HTMLParser()
        abstract = ""
        for abstract_element in self.tree.xpath('.//Abstract/AbstractText'):
            if abstract_element.get('Label'):
                abstract += "%s: %s\n" % (abstract_element.get('Label').upper(), abstract_element.text)
            else:
                abstract += "%s\n" % abstract_element.text
        language = _get_one_element(self.tree.xpath('.//Article/Language/text()'))
        # if language:
        #     language = language[0:2].lower()
        # else:
        # TODO: Save Original language
        abstract = parser.unescape(abstract)
        language = 'en'
        title = _get_one_element(self.tree.xpath('.//BookTitle/text()' if self.is_book else './/ArticleTitle/text()'))
        return {
            language: {
                'title': to_utf8(title),
                'abstract': to_utf8(abstract),
                'copyright': '',
                'translation_status': 'blocked'
            }
        }

    def _parse_year(self):
        return self.year

    def _parse_comments_on(self):
        return _get_one_element(
            self.tree.xpath('.//CommentsCorrectionsList/CommentsCorrections[@RefType="CommentOn"]/PMID/text()')
        )

    def prepare_multiple(self, data):
        _tree = get_tree(data.replace('xmlns="http://www.w3.org/1999/xhtml"', ''))

        for _doc in [_d for _d in _tree.xpath('//PubmedArticle')]:
            self.tree = _doc
            self.is_book = len(self.tree.xpath('//PubmedBookArticle')) == 1
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
                comments_on = self._parse_comments_on()
                if comments_on is not None:
                    document_json['info']['comments_on'] = comments_on

            documents_json.append(document_json)

        return documents_json


    def parse(self, xml):
        try:
            xml = xml.decode('utf-8')
        except Exception:
            pass
        self.is_book = '<PubmedBookArticle>' in xml
        BaseParser.prepare(self, xml.encode('utf-8'))

        status, msg = self.validate()
        if not status:
            document_json = {'error': msg}
        else:
            document_json = BaseParser.get_json(self)
            for key, value in self.ids.iteritems():
                document_json['info']['ids'][key] = value
            comments_on = self._parse_comments_on()
            if comments_on is not None:
                document_json['info']['comments_on'] = comments_on

        return document_json

    def parse_pmid(self, pmid):
        http_connection = Http()
        url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=xml"
        response, content = http_connection.request(url % pmid, "GET")
        redirect = re.search(r'<meta.*http-equiv=\"Refresh\".+url=([^ ;]+).*\".*\/>', content)
        if redirect:
            return self.parse_pmid(redirect.groups()[0])

        # content = Pubmed.unescape(content.decode('utf-8'))
        return self.parse(content)

    def parse_from_id_or_url(self, id_or_url):
        pmid = id_or_url
        if len(id_or_url.split('/')) > 1:  # Is a URL
            pmid = id_or_url.split('/')[-1]
        return self.parse_pmid(pmid)

    def parse_url(self, url):
        return self.parse_from_id_or_url(url)

    # TODO: improve this static method, meanwhile was created for RSS test
    # @staticmethod
    # def is_valid_url(url):
    #     if url is not None:
    #         return 'http://www.ncbi.nlm.nih.gov/PubMed/' in url or 'http://www.ncbi.nlm.nih.gov/pubmed/' in url
    #     return False
