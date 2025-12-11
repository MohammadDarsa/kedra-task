import argparse
import scrapy
import logging
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from src.models.case import Case
from src.settings import get_settings
from src.utils.date_utils import generate_date_ranges

class WrcSpider(scrapy.Spider):
    name = 'wrc'
    allowed_domains = ['workplacerelations.ie']
    start_urls = ['https://www.workplacerelations.ie/en/search/']

    def __init__(self, q='', from_date='', to_date='', body_filter='', *args, **kwargs):
        super(WrcSpider, self).__init__(*args, **kwargs)
        self.query = q
        try:
            self.start_date = datetime.strptime(from_date, "%d/%m/%Y")
            self.end_date = datetime.strptime(to_date, "%d/%m/%Y")
        except ValueError:
            self.ranges = []
        else:
            self.ranges = generate_date_ranges(self.start_date, self.end_date)
            
        self.body_filter = body_filter

    def parse(self, response):
        if not self.ranges:
             self.logger.warning("no valid date ranges to scrape.")
             return

        for r_start, r_end in self.ranges:
            s_str = r_start.strftime("%d/%m/%Y")
            e_str = r_end.strftime("%d/%m/%Y")
            
            formlist = []
            # only select the specific body for this spider instance
            # first time I noticed about how .NET forms name the fields
            if self.body_filter == 'Employment Appeals Tribunal':
                formlist.append(('ctl00$ContentPlaceHolder_Main$CB2$CB2_0', '2'))
            elif self.body_filter == 'Equality Tribunal':
                formlist.append(('ctl00$ContentPlaceHolder_Main$CB2$CB2_1', '1'))
            elif self.body_filter == 'Labour Court':
                formlist.append(('ctl00$ContentPlaceHolder_Main$CB2$CB2_2', '3'))
            elif self.body_filter == 'Workplace Relations Commission':
                 formlist.append(('ctl00$ContentPlaceHolder_Main$CB2$CB2_3', '4'))
            
            formdata = {
                'ctl00$ContentPlaceHolder_Main$TextBox1': self.query,
                'ctl00$ContentPlaceHolder_Main$TextBox2': s_str,
                'ctl00$ContentPlaceHolder_Main$TextBox3': e_str,
            }
            
            for key, value in formlist:
                 formdata[key] = value

            self.logger.info(f"submitting search for partition {s_str} - {e_str} (body: {self.body_filter})")

            yield scrapy.FormRequest.from_response(
                response,
                formid='form',
                formdata=formdata,
                clickdata={'name': 'ctl00$ContentPlaceHolder_Main$refine_btn'},
                callback=self.parse_results,
                meta={'partition_date': r_start.strftime("%m/%Y")},
                dont_filter=True
            )



    def parse_results(self, response):
        partition_date = response.meta.get('partition_date')
        
        for result in response.css('li.each-item'):
             item = Case()
             link = result.css('h2.title a::attr(href)').get()
             if link:
                 url = response.urljoin(link)
                 item['url'] = url
                 ref_num = result.css('span.refNO::text').get()
                 item['ref_number'] = ref_num.strip() if ref_num else None
                 item['published_date'] = result.css('span.date::text').get()
                 item['description'] = result.css('p.description::text').get()
                 item['partition_date'] = partition_date
                 item['scraped_at'] = datetime.utcnow()
                 item['body_filters'] = [self.body_filter] if self.body_filter else []
                 
                 # visit the page to get attachments
                 yield scrapy.Request(
                     url, 
                     callback=self.parse_decision, 
                     meta={'item': item}
                 )
        
        next_page = response.css('ul.pager li:last-child a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse_results, meta=response.meta)

    def parse_decision(self, response):
        item = response.meta['item']
        
        additional_files = []
        content_div = response.css('div.col-sm-9')
        
        # now this logic to get nested links / attachments is not ideal or recursive as I'd love it to be but due to time constraints I won't be spending more time on this. It works fine but can be done better.
        for a in content_div.css('a'):
            href = a.attrib.get('href')
            if not href:
                continue
                
            full_url = response.urljoin(href)

            if 'search' in full_url.lower():
                continue
            if full_url == response.url:
                 continue
            if full_url.endswith('#'):
                 continue
                 
            additional_files.append(full_url)
            
        item['additional_files'] = list(set(additional_files)) # deduplicate
        yield item

def main():
    parser = argparse.ArgumentParser(description='run wrc scrapy spider')
    parser.add_argument('--q', type=str, default='', help='search query')
    parser.add_argument('--from_date', type=str, default='', help='from date (dd/mm/yyyy)')
    parser.add_argument('--to_date', type=str, default='', help='to date (dd/mm/yyyy)')
    parser.add_argument('--bodies', type=str, default='', help='comma-separated list of bodies')
    parser.add_argument('--debug', action='store_true', help='enable debug logging')
    
    args = parser.parse_args()
    
    # disable annoying logs (only keeps warnings and errors)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass

    settings = get_settings(debug=args.debug)
    process = CrawlerProcess(settings)
    
    # here I was confused if I should do all bodies (each in spider) or just the user should specify the bodies, so I did the logic for both.
    if args.bodies:
        bodies_list = [b.strip() for b in args.bodies.split(',')]
    else:
        bodies_list = [
            'Employment Appeals Tribunal',
            'Equality Tribunal',
            'Labour Court',
            'Workplace Relations Commission'
        ]
    
    for body in bodies_list:
        process.crawl(WrcSpider, q=args.q, from_date=args.from_date, to_date=args.to_date, body_filter=body)
    
    process.start()

if __name__ == '__main__':
    main()
