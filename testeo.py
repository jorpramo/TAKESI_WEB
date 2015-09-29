__author__ = 'jpradas'
#!/usr/bin/python
# -*- coding: utf-8 -*-

import pymongo
import mongodb
import Documento
import settings as set
import sys
import logging
import Utils
from Utils import utilidades
from flask import Flask, redirect, request, url_for
from flask import render_template
from flask_admin import Admin
import flask_admin as admin
from wtforms import form, fields
from flask_admin.contrib.pymongo import ModelView
from bson.objectid import ObjectId

import datetime
import time

def busqueda_resp(pregunta):

    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    #db.DOCS.createIndex({"tags_vocab":"text", "texto": "text", "nombre": "text", "tags":"text"},{"name":"indice", "weights":{"tags_vocab":4, "texto":10, "nombre": 8, "tags":5, }},{ default_language: "spanish" })
    result=DOC.find({ "$text": { "$search": pregunta, "$language": "es"}}, {"_id":1, "nombre": 1,"texto":1,  "score": { "$meta":"textScore"}}).sort([('score', {'$meta': 'textScore'})]).limit(set.TOTAL_DOCUMENTOS)
    total=DOC.find({}).count()
    return result, total

def procesado():
    f = open('resultados', 'a')
    total=0
    Preguntas=[u'Como se da de alta un interlocutor en Ediwin',u'como localizar un mensaje rechazado en el AS2', u'Que estado es una publicacion confirmada',u'como se configura un certificado en ediwin',u'como se configura un interlocutor en el EOS']
    stops=Utils.get_stops()

    for p in Preguntas:
        inicio=datetime.datetime.now()
        pregunta=p.lower()
        pregunta_2=utilidades.SinStopwords(pregunta, stops)
        pregunta_2=utilidades.Stemming(pregunta_2)

        result=busqueda_resp(pregunta_2)
        respuestas=result[0]
        total=result[1]
        inicio_=datetime.datetime.now()
        preparacion=inicio_-inicio
        for d in respuestas:
            doc=Documento.Document(d)
            inicio1=datetime.datetime.now()
            doc.similaridad(p)
            inicio2=datetime.datetime.now()
            alg1=inicio2-inicio1
            doc.similaridad_NLTK_tf_idf(p, stops)
            inicio3=datetime.datetime.now()
            alg2=inicio3-inicio2
            doc.similaridad_cosine(p)
            alg3=datetime.datetime.now()-inicio3
            f.write(str(total) + ',' + str(preparacion) + ',' + str(alg1)+ ',' + str(alg2)+ ',' + str(alg3) + '\n')


while (True):
    procesado()
    time.sleep(120)