import pymongo
import logging

class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI', 'mongodb://root:mongopasswords@localhost:27017/'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'wrc_db')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        collection_name = 'wrc_decisions'
        item_dict = dict(item)
        body_filters = item_dict.pop('body_filters', [])
        
        update_op = {
            '$addToSet': {'body_filters': {'$each': body_filters}},
            '$set': item_dict
        }

        if item_dict.get('ref_number'):
            self.db[collection_name].update_one(
                {'ref_number': item_dict['ref_number']},
                update_op,
                upsert=True
            )
        elif item_dict.get('url'): # fallback mechanism if ref number is not available
            self.db[collection_name].update_one(
                {'url': item_dict['url']},
                update_op,
                upsert=True
            )
            
        return item
