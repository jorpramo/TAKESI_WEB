__author__ = 'Jorge'

import pymongo
import settings as set
from bson.code import Code

class stats(object):
    def __init__(self, db='docs',
                 collection='DOCS'):

        self.conn = pymongo.MongoClient(set.MONGODB_URI)
        self.collection = self.conn[db][collection]

    def get_data_cloud(self):
        self.collection = self.conn['docs']['CLOUD']
        result = self.collection.find()
        words=[]
        for doc in result.find().sort('value', pymongo.DESCENDING).limit(200):
            words.append([doc['_id'], doc['value']])
        return words

    def get_data_mapa(self):

        result = self.collection.find().distinct("f1")
        label=[]
        for record in result:
            label.append(record)
        return  label



