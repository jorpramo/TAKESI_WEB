# -*- coding: utf-8 -*-
__author__ = 'jpradas'

import math
import pymongo
import settings as set
from nltk.text import TextCollection
from bson.objectid import ObjectId

from Utils import utilidades
import datetime

class Document(object):
    def __init__(self, result):
        print('Inicio: ' + str(datetime.datetime.now()))
        self.id=result['_id']
        self.nombre = result['nombre']
        self.score = result['score']
        #self.sents = nltk.sent_tokenize(result['texto'],language='spanish')
        lines=result['texto'].split(".")
        parrafo=[]
        total=[]
        lines=[s for s in lines if len(s)>20]
        print('Fin lineas: ' + str(datetime.datetime.now()))
        for l in range(len(lines)):
            parrafo.append(lines[l])
            if l%5 == 0:
                total.append(parrafo)
                parrafo=[]
        total.append(parrafo)
        print('Fin Parrafo: ' + str(datetime.datetime.now()))
        self.sents = total
        self.texto = result['texto']
        self.totalsentencias = 0
        self.sentenciascontermino = 0
        print('Fin asignacion: ' + str(datetime.datetime.now()))
        self.encontrado()
        print('Fin actualizacion: ' + str(datetime.datetime.now()))

    #def cargadoc(self, cursor):
    #    for x in cursor:
    def similaridad(self, pregunta):
        resultado=[]
        sentencias=[s for s in self.sents if len("".join(s))>200]
        #sentencias = self.sents
        self.totalsentencias=len(sentencias)

        IDF=1
        for s in sentencias:
            resultado.append([s,self.calcula_similaridad(s,pregunta)])

        try:
            IDF=math.log(self.totalsentencias / (self.sentenciascontermino))
        except:
            print("Division por cero")
        for row in resultado:
            row[1]=row[1]/IDF
        registro=[]
        resultado=sorted(resultado, key=lambda res: res[1],reverse=True)
        final=resultado[:3]
        for v in final:
            registro.append([v[0],v[1],self.nombre])
        return [registro]

    def calcula_similaridad(self, sent, pregunta):
        rank = self.score
        q = pregunta
        text = sent

        #q = utilidades.SinStopwords(q)
        text = utilidades.SinStopwords("".join(text))
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
        score = score * rank
        return TF


    def encontrado(self):
        client = pymongo.MongoClient(set.MONGODB_URI)
        db = client.docs
        DOC=db.DOCS
        DOC.update({'_id':self.id}, {'$inc': {'enc': 1}, '$set':  {"fecha": datetime.datetime.utcnow()}})


    def similaridad_NLTK_tf_idf(self, pregunta):
        resultado=[]
        #sentencias=self.sents
        sentencias=[s for s in self.sents if len("".join(s))>100]
        self.totalsentencias=len(sentencias)
        texto=TextCollection(self.texto)

        for s in sentencias:
            resultado.append([s,texto.tf_idf(pregunta," ".join(s))])

        resultado=sorted(resultado, key=lambda res: res[1])
        final=resultado[-3]
        punt=final[1]
        cadena=final[0]
        return [cadena, punt]

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
