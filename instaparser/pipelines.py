# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('127.0.0.1', 27017)
        self.mongobase = client.instagram

    def process_item(self, item, spider):
        collection = self.mongobase[f'{item["from_user"]}-{item["type"]}']
        try:
            collection.insert_one(item)
        except DuplicateKeyError:
            pass
        return item
