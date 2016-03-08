# -*- coding: utf-8 -*-
import re
from datetime import datetime as dt
from time import sleep, strftime
import urllib

from .base_crawler import BaseCrawler
from .vhl_parser import VHL
from .general import batch_gen

class VhlCrawler(BaseCrawler):

    default_query = ''
    base_url = "http://search.bvsalud.org/portal/?output=xml&lang=en&sort=&format=summary&fb=&page=1&filter[db][]=LILACS&filter[type_of_study][]=systematic_reviews&q=%s&index=tw"
    base_document_url = "http://search.bvsalud.org/portal/?output=xml&lang=en&from=&sort=&format=&count=&fb=&page=1&q=id:%s&index=tw"

    def __init__(self):
        super(VhlCrawler, self).__init__()
        self.documents = []
        self.ids = []

    def _parser(self):
        return VHL()

    def parse_ids(self, strategy=None, min_year=2010, max_year=None, limit=None):
        self.ids = []
        self.parse_documents(strategy=strategy, min_year=min_year, max_year=max_year, limit=limit)

        for docs in batch_gen(self.documents, 50):
            for d in docs:
                self.ids.append(d['info']['ids']['vhl'])
        return self.ids

    def parse_documents(self, strategy=None, min_year=2010, max_year=None, limit=None):
        url = VhlCrawler.base_url % (strategy or VhlCrawler.default_query)
        url += "&" + VhlCrawler._year_range_filter(min_year, (max_year or dt.now().year) )

        BULK = 100
        count = None
        documents = []
        j = 0

        while True:
            limit_bulk = BULK if (not limit or (limit and BULK < limit)) else limit
            # import ipdb, pprint; ipdb.set_trace()
            response, content = self.parse_url(url + "&from=%s&count=%s" % (j*BULK+1, limit_bulk))
            if not count:
                count = int(self.tree.xpath("//result[@numFound]")[0].attrib.get('numFound'))
                if not limit:
                    limit = count

            documents.extend(self._parser().parse_multiple(content))

            if j*BULK+1 + limit_bulk > min(count, limit):
                break
            j += 1
            sleep(0.3)

        self.documents = documents
        return documents

    @staticmethod
    def _year_range_filter(min_year, max_year):
        years = range(min_year, max_year+1)
        return '&'.join(map(lambda y: "filter[year_cluster][]="+str(y), years))
