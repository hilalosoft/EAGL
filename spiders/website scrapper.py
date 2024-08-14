import scrapy
import pandas as pd


class QuotesSpider(scrapy.Spider):
    name = "quotes"

    def start_requests(self):
        urls = [
            'https://www.htmlstrip.com/alexa-top-1000-most-visited-websites',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-2]
        string_list = response.css('div.col-6::text').getall()
        domain_list = []
        for i in range(3, 2002, 2):
            domain_list.append(string_list[i][1:])
        df_depth = pd.DataFrame(domain_list)
        # if not os.path.isfile('list.csv'):
        df_depth.to_csv('websites.csv',
                        header=["Page"],
                        index=False)
        self.log(f'Saved file websites.csv')
