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
        map = Code("function m() { for(var i in this.cloud)  {emit(this.cloud[i].word, this.cloud[i].total);}}")
        reduce = Code("function(key, values) { return Array.sum(values);};")
        result = self.collection.map_reduce(map, reduce, "myresults")
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



