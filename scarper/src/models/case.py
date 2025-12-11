import scrapy

class Case(scrapy.Item):
    ref_number = scrapy.Field()
    published_date = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    partition_date = scrapy.Field()
    file_path = scrapy.Field()
    file_hash = scrapy.Field()
    scraped_at = scrapy.Field()
    additional_files = scrapy.Field()
    body_filters = scrapy.Field()
