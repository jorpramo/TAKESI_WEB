# -*- coding: utf-8 -*-
__author__ = 'jpradas'

import sys
import codecs
import nltk
import math

from Utils import utilidades

class Document(object):

    def __init__(self, result):
        print(result.keys())
        self.nombre = result['nombre']
        self.score = result['score']
        #self.sents = nltk.sent_tokenize(result['texto'],language='spanish')
        lines=result['texto'].split(".")
        parrafo=[]
        total=[]
        for l in range(len(lines)):
            parrafo.append(lines[l])
            if l%5 == 0:
                total.append(parrafo)
                parrafo=[]
        total.append(parrafo)
        self.sents = total
        self.texto = result['texto']
        self.totalsentencias = 0
        self.sentenciascontermino = 0

    #def cargadoc(self, cursor):
    #    for x in cursor:
    def similaridad(self, pregunta):
        resultado=[]
        sentencias=[s for s in self.sents if len(s)>100]
        print("Total Sentencias")
        self.totalsentencias=len(sentencias)
        print(len(sentencias))
        for s in sentencias:
            resultado.append([s,self.calcula_similaridad(s,pregunta)])

        try:
            IDF=math.log(self.totalsentencias / (self.sentenciascontermino))
        except:
            print("Division por cero")
        for row in resultado:
            row[1]=row[1]/IDF
            #print(row[1])
        resultado=sorted(resultado, key=lambda res: res[1])

        return resultado[-1]

    def calcula_similaridad(self, sent, pregunta):
        rank = self.score
        q = pregunta
        text = sent
        #try:
        #    print(sent)
        #except:
        #    print("no se puede escribir")


        # Remove stopwords from question and passage
        # and split it into words
        q = utilidades.SinStopwords(q)
        text = utilidades.SinStopwords(text)
        q = utilidades.Stemming(q)
        text = utilidades.Stemming(text)
        q=q.split()
        text=text.split()
        # Filter all words in passage that they are
        # not present in question
        words = list(filter(lambda x: x in q, text))
        #print(words)
        # Our initial score is the number of coincidences
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




