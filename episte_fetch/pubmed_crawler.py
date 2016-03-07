# -*- coding: utf-8 -*-
import re
from time import sleep, strftime
import urllib

from .base_crawler import BaseCrawler
from .pubmed_parser import Pubmed
from .general import batch_gen

class PubmedCrawler(BaseCrawler):

    default_query = urllib.quote('''(MEDLINE[Title/Abstract]+OR+(systematic[Title/Abstract]+AND+review[Title/Abstract])+OR+meta+analysis[Publication+Type])+NOT+("The+Cochrane+database+of+systematic+reviews"[Journal])''', safe="()*+")
    base_url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=%s&datetype=PDAT&sort=pub+date"
    base_document_url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=xml"

    def __init__(self):
        super(PubmedCrawler, self).__init__()

    def _parser(self):
        return Pubmed()

    def parse_ids(self, strategy=None, mindate="2010/01/01", maxdate=None, limit=None):
        self.ids = self._get_all_ids(strategy=strategy, mindate=mindate, maxdate=maxdate, limit=limit)
        return self.ids

    def parse_documents(self, strategy=None, mindate="2010/01/01", maxdate=None, limit=None):
        self.ids = self._get_all_ids(strategy=strategy, mindate=mindate, maxdate=maxdate, limit=limit)

        BULK = 100
        limit = limit if limit is not None else len(self.ids)
        documents = []

        for ids_bulk in batch_gen(self.ids, BULK):
            response, content = self.parse_url(PubmedCrawler.base_document_url % ','.join(ids_bulk))
            documents.extend(self._parser().parse_multiple(content))

        self.documents = documents
        return documents

    def _get_all_ids(self, strategy=None, mindate="2010/01/01", maxdate=None, limit=None):
        url = PubmedCrawler.base_url % (strategy or PubmedCrawler.default_query)
        url += '&mindate=%s' % mindate

        if not maxdate:
            maxdate = strftime('%Y/%m/%d')
        url += '&maxdate=%s' % maxdate

        _ids = []
        retmax = 5000
        count = None
        j = 0

        while True:
            self.parse_url(url + "&retstart=%s&retmax=%s" % (j*retmax, retmax))
            if not count:
                count = int(self.tree.xpath("//eSearchResult/Count/text()")[0])

            ids = [x.xpath("./text()")[0] for x in self.tree.xpath("//IdList/Id")]
            _ids.extend(ids)

            if j * retmax > count:
                break
            if limit and j * retmax >= limit:
                break
            j += 1
            sleep(0.6) # >0.3, as stated by http://www.ncbi.nlm.nih.gov/books/NBK25497/#chapter2.Usage_Guidelines_and_Requiremen

        return _ids[:limit] if limit else _ids


