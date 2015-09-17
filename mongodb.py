import pymongo
import nltk
import nltk.data
import datetime
from nltk.data import LazyLoader
from nltk.tokenize import TreebankWordTokenizer
from nltk.util import AbstractLazySequence, LazyMap, LazyConcatenation
from nltk import word_tokenize

class BagWords:
    def __init__(self, host='localhost', port=27017, db='docs', collection='BAGWORDS'):
        MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
        #MONGODB_URI = 'mongodb://localhost:27017/'
        self.conn = pymongo.MongoClient(MONGODB_URI)
        self.collection = self.conn[db][collection]
    def LeeBagWords(self):
        #MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
        tags=self.collection.find(projection={"_id":0})
        print(tags.count())
        vector=[]
        for t in tags:
            for i,j in t.items():
                    vector.append(j)
            #data=json.loads(t)
            #print(data['tag'])
        return vector
#MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'

def busqueda_resp(pregunta, indices):
    #MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.docs
    indices=db.DOCS



class MongoDBPreguntas(object):
    def __init__(self, host='localhost', port=27017, db='docs',
                 collection='PREGUNTAS'):
        MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
        #MONGODB_URI = 'mongodb://localhost:27017/'

        self.conn = pymongo.MongoClient(MONGODB_URI)
        self.collection = self.conn[db][collection]

    def inserta_pregunta(self, pregunta):
        post = {"pregunta": pregunta, "fecha": datetime.datetime.utcnow(),"count":1}
        id=self.collection.find_one_and_update({'pregunta':pregunta}, {'$inc': {'count': 1}, '$set':  {"fecha": datetime.datetime.utcnow()}},upsert=True)

        #self.collection.insert_one(post).inserted_id



class MongoDBLazySequence(AbstractLazySequence):
    def __init__(self, host='localhost', port=27017, db='docs',
                 collection='DOCS', field='texto'):
        #MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
        MONGODB_URI = 'mongodb://localhost:27017/'

        self.conn = pymongo.MongoClient(MONGODB_URI)
        self.collection = self.conn[db][collection]
        self.field = field

    def __len__(self):
        return self.collection.count()

    def iterate_from(self, start):
        f = lambda d: d.get(self.field, '')
        return iter(LazyMap(f, self.collection.find(filter={"_id": "55dc542d373a921f447408c9"} ,projection=[self.field], skip=start)))


class MongoDBCorpusReader(object):
    def __init__(self, word_tokenizer=TreebankWordTokenizer(),
                 sent_tokenizer=LazyLoader('tokenizers/punkt/spanish.pickle'), **kwargs):
        self._seq = MongoDBLazySequence(**kwargs)
        self._word_tokenize = word_tokenizer.tokenize
        self._sent_tokenize = sent_tokenizer.tokenize

    def text(self):
        return self._seq

    def words(self):
        return LazyConcatenation(LazyMap(self._word_tokenize, self.text()))

    def sents(self):
        return LazyConcatenation(LazyMap(self._sent_tokenize, self.text()))



    def localizar(self, cadena="Ficha"):
        result=''
        left_margin = 10
        right_margin = 10
        for t in self.text():
            tokens = word_tokenize(t)
            text = nltk.Text(tokens)
            ## Collect all the index or offset position of the target word
            c = nltk.ConcordanceIndex(text.tokens, key = lambda s: s.lower())
            ## Collect the range of the words that is within the target word by using text.tokens[start;end].
            ## The map function is use so that when the offset position - the target range < 0, it will be default to zero
            concordance_txt = ([text.tokens[list(map(lambda x: x-5 if (x-left_margin)>0 else 0,[offset]))[0]:offset+right_margin] for offset in c.offsets(cadena)])

            ## join the sentences for each of the target phrase and return it
            result=[''.join([x+' ' for x in con_sub]) for con_sub in concordance_txt]

        return result


    def localizar_2(self, cadena="Ficha"):
        left_margin = 10
        right_margin = 10
        for t in self.text():
            tokens = word_tokenize(t)
            text = nltk.Text(tokens)
            ## Collect all the index or offset position of the target word
            c = nltk.ContextIndex(text.tokens, key = lambda s: s.lower())
            c1 = nltk.ConcordanceIndex(text.tokens, key = lambda s: s.lower())
            fd=c.common_contexts(cadena)
            print(fd)
            print(cadena)

        return fd


