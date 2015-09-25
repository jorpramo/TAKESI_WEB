# -*- coding: utf-8 -*-
__author__ = 'jpradas'

import math
import pymongo
import settings as set
import Utils
from bson.objectid import ObjectId
from math import log
from nltk import word_tokenize
from Utils import utilidades
import datetime
from text_comparer.vectorizer import compare_texts
from nltk.corpus import PlaintextCorpusReader

class TextoCollection(object):
    """A collection of texts, which can be loaded with list of texts, or
    with a corpus consisting of one or more texts, and which supports
    counting, concordancing, collocation discovery, etc.  Initialize a
    TextCollection as follows:

    Iterating over a TextCollection produces all the tokens of all the
    texts in order.
    """
    def __init__(self, source, name=None):
        if hasattr(source, 'words'): # bridge to the text corpus reader
            source = [source.words(f) for f in source.fileids()]

        self._texts = source.split()
        #Texto.__init__(self, LazyConcatenation(source))
        self.idf_cache = {}

    def tf(self, term, text, method=None):
        """ The frequency of the term in text. """
        return text.count(term) / len(text)

    def idf(self, term, method=None):
        """ The number of texts in the corpus divided by the
        number of texts that the term appears in.
        If a term does not appear in the corpus, 0.0 is returned. """
        # idf values are cached for performance.
        idf = self.idf_cache.get(term)
        if idf is None:
            matches = len([True for text in self._texts if term in text])
            # FIXME Should this raise some kind of error instead?
            idf = (log(float(len(self._texts)) / matches) if matches else 0.0)
            self.idf_cache[term] = idf
        return idf

    def tf_idf(self, term, text):
        return self.tf(term, text) * self.idf(term)

class Document(object):
    def __init__(self, result):

        self.id=result['_id']
        self.nombre = result['nombre']
        self.score = result['score']
        #self.sents = nltk.sent_tokenize(result['texto'],language='spanish')
        lines=result['texto'].split(".")
        parrafo=[]
        total=[]
        lines=[s for s in lines if len(s)>set.MINIMO_LINEAS]

        for l in range(len(lines)):
            parrafo.append(lines[l])
            if l%set.TOTAL_LINEAS == 0:
                total.append(parrafo)
                parrafo=[]
        total.append(parrafo)

        self.sents = total
        self.texto = result['texto']
        self.totalsentencias = 0
        self.sentenciascontermino = 0
        self.encontrado()

    #def cargadoc(self, cursor):
    #    for x in cursor:
    def similaridad(self, pregunta):
        resultado=[]
        sentencias=[s for s in self.sents if len("".join(s))>set.SIZE_PARRAFOS]
        #sentencias = self.sents
        self.totalsentencias=len(sentencias)

        IDF=1
        for s in sentencias:
            resultado.append([s,self.calcula_similaridad(s,pregunta)])

        try:
            IDF=math.log(self.totalsentencias / (1 + (self.sentenciascontermino)))
        except:
            print("Division por cero")
        for row in resultado:
            row[1]=row[1]*IDF # No seria multiplicacion
        registro=[]
        resultado=sorted(resultado, key=lambda res: res[1],reverse=True)
        final=resultado[:set.TOTAL_RESPUESTAS]
        for v in final:
            registro.append([v[0],v[1],self.nombre])
        return [registro]

    def calcula_similaridad(self, sent, pregunta):
        rank = self.score
        q = pregunta
        text = sent
        stops=Utils.get_stops()
        #q = utilidades.SinStopwords(q)
        text = utilidades.SinStopwords("".join(text), stops)
        #q = utilidades.Stemming(q)
        text = utilidades.Stemming("".join(text))
        q=q.split()
        text=text.split()

        words = list(filter(lambda x: x in q, text))

        score = len(words)
        try:
            TF= len(words)/len(text)
        except:
            TF=0
        if (score>0):
            self.sentenciascontermino=self.sentenciascontermino+1
        # Weight score by rank
        #score = score * rank
        return TF


    def encontrado(self):
        client = pymongo.MongoClient(set.MONGODB_URI)
        db = client.docs
        DOC=db.DOCS
        DOC.update({'_id':self.id}, {'$inc': {'enc': 1}, '$set':  {"fecha": datetime.datetime.utcnow()}})


    def similaridad_NLTK_tf_idf(self, pregunta, stops):

        #sentencias=self.sents
        sentencias=[s for s in self.sents if len("".join(s))>set.SIZE_PARRAFOS]
        self.totalsentencias=len(sentencias)
        texto=self.texto

        text = utilidades.SinStopwords("".join(texto), stops)
        #q = utilidades.Stemming(q)
        text = utilidades.Stemming("".join(text))
        pregunta=pregunta.split()
        texto=TextoCollection(text)
        acum = 1

        resultado=[]
        for s in sentencias:
            cadena=" ".join(s).lower()
            acum=sum((texto.tf_idf(d,(cadena)) for d in pregunta))
            resultado.append([s,acum])

        resultado=sorted(resultado, key=lambda res: res[1] ,reverse=True)
        final=resultado[:set.TOTAL_RESPUESTAS]
        registro=[]
        for v in final:
            registro.append([v[0],v[1],self.nombre])
        return [registro]

    def similaridad_cosine(self, pregunta):
        sentencias=[s for s in self.sents if len("".join(s))>set.SIZE_PARRAFOS]
        self.totalsentencias=len(sentencias)

        resultado=[]
        for s in sentencias:
             cadena=" ".join(s).lower()
             resultado.append([s,compare_texts(pregunta,cadena)])

        resultado=sorted(resultado, key=lambda res: res[1] ,reverse=True)
        final=resultado[:set.TOTAL_RESPUESTAS]
        registro=[]
        for v in final:
            registro.append([v[0],v[1],self.nombre])
            return [registro]

class estados(object):
    def __init__(self, id):
        client = pymongo.MongoClient(set.MONGODB_URI)
        db = client.docs
        self.id=id
        self.DOC=db.DOCS

    def positivo(self):
        self.DOC.update_one({'_id':ObjectId(self.id)}, {'$inc': {'pos': 1}})

    def negativo(self):
        self.DOC.find_one_and_update({'_id':ObjectId(self.id)},  {'$inc': {'neg': 1}})
