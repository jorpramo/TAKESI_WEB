# -*- coding: utf-8 -*-

import pymongo
import mongodb
import Documento
import settings as set
from Utils import utilidades
from flask import Flask, redirect, request, url_for
from flask import render_template, jsonify
from flask_admin import Admin
import flask_admin as admin
from wtforms import form, fields
from flask_admin.contrib.pymongo import ModelView, filters
from bson.objectid import ObjectId
from bson.son import SON
import datetime
from estadisticas import stats
from bson.json_util import dumps

def busqueda_indices(tags):
    indices=db.INDEX
    list=indices.find({"tag_vocab" : { '$in': tags}}, projection={"id_doc":1,"_id":0})
    result=[]
    for record in list:
            result.append(record)
    return result

def busqueda_resp(pregunta):

    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    #db.DOCS.createIndex({"tags_vocab":"text", "texto": "text", "nombre": "text", "tags":"text"},{"name":"indice", "weights":{"tags_vocab":4, "texto":10, "nombre": 8, "tags":5, }},{ default_language: "spanish" })
    result=DOC.find({ "$text": { "$search": pregunta, "$language": "es"}}, {"_id":1, "nombre": 1,"texto":1,  "score": { "$meta":"textScore"}}).sort([('score', {'$meta': 'textScore'})]).limit(set.TOTAL_DOCUMENTOS)
    return result



# Create application
app = Flask(__name__)
# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'


client = pymongo.MongoClient(set.MONGODB_URI)
db = client.docs
DOCS=db.docs

reader = mongodb.MongoDBCorpusReader()
writer = mongodb.MongoDBPreguntas()
bw = mongodb.BagWords()

# User admin
class InnerForm(form.Form):
    name = fields.TextField('Búsqueda')


class CorpusForm(form.Form):
    Nombre = fields.TextField('Nombre')
    num_words = fields.TextField('num_words')
    enc = fields.TextField('enc')
    pos = fields.TextField('pos')
    neg = fields.TextField('neg')


class CorpusView(ModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_list = ('nombre', 'num_words', 'enc', 'pos', 'neg')
    column_sortable_list = ('nombre', 'num_words', 'enc', 'pos', 'neg')
    form = CorpusForm

# Flask views
@app.route('/')
def index():
    return render_template('index_takesi.html') 

@app.route('/doc/neg/<id>')
def pos_neg(id):
    estado=Documento.estados(id)
    estado.negativo()
    print("negativo")
    return 'Negativo'

@app.route('/doc/pos/<id>')
def pos_doc(id):
    estado=Documento.estados(id)
    estado.positivo()
    print("positivo")
    return 'Positivo'

@app.route('/listadoc/<cadena>')
def listadoc(cadena):
    print(cadena)
    cadena=cadena.lower()
    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    result=DOC.find({ "$text": { "$search": cadena, "$language": "es"}}, {"_id":0, "nombre": 1, "score": { "$meta":"textScore"}}).sort([('score', {'$meta': 'textScore'})])
    tags=db.DOCS.aggregate([{"$match": {"tags_vocab":cadena}},{"$group":{"_id":"$nombre","total":{"$sum":1}}}])
    resultado=[]

    for t in tags:
        score=0
        result.rewind()
        for s in result:
            if s["nombre"]==t["_id"]:
                score=s['score']
        resultado.append([t["_id"],score])

    resultado=sorted(resultado, key=lambda resultado: resultado[1], reverse=True)
    data=dumps(resultado)
    print(data)
    return data

@app.route('/doc/<id>')
def show_doc(id):
    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    results=DOC.find({"_id": ObjectId(id)}, {"nombre" :1,"_id":0})
    for doc in results:
        file=doc['nombre'].replace('.txt', '.pdf')
    return redirect(url_for('static', filename="PDF/"+file))


@app.route('/stats/')
def estadisticas():

    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    pipeline = [{"$unwind":"$tags_vocab"},{"$group":{"_id":"$tags_vocab", "total":{"$sum":1}}},{"$sort":{"total":-1}}]
    data=dumps(list(DOC.aggregate(pipeline)))

    return data


@app.route('/busqueda', methods=['POST'])
def busqueda():
    print('Inicio: ' + str(datetime.datetime.now()))
    pregunta=request.form['text']
    pregunta_2=utilidades.SinStopwords(pregunta)
    pregunta_2=utilidades.Stemming(pregunta_2)
    print('Fin ofrmateo pregunta: ' + str(datetime.datetime.now()))
    writer.inserta_pregunta(pregunta_2)
    print('Fin insercion pregunta: ' + str(datetime.datetime.now()))
    respuestas=busqueda_resp(pregunta_2)
    print('Fin busq respuestas 1: ' + str(datetime.datetime.now()))
    docs=respuestas.clone()
    text=[]
    text2=[]
    for d in docs:
        doc=Documento.Document(d)
        print('Inicio Iteracion DOC: ' + str(datetime.datetime.now()))
        registro=doc.similaridad(pregunta_2)
        for r in registro:
            for s in r:
                text.append(s)
        print('Fin Iteracion DOC: ' + str(datetime.datetime.now()))
    text=sorted(text, key=lambda text: text[1], reverse=True)
    linea=[]
    print('Inicio Iteracion tuplas: ' + str(datetime.datetime.now()))
    for tupla in text[:5]:
        linea.append([tupla[0],tupla[1],tupla[2]])

    print('Fin Iteracion tuplas: ' + str(datetime.datetime.now()))
    return render_template('resultados.html',  resps=respuestas, entries=linea, question=pregunta)

@app.route('/graph/')
def home():
    """ Simply serve our chart page """
    return render_template('chart1.html')


@app.route('/graphcloud/')
def graphcloud():
    s=stats()
    result=s.get_data_cloud()
    return render_template('cloud.html', output=result)

@app.route('/graphmap/')
def graphmap():
    s=stats(collection="SIMILITUD")
    result=s.get_data_mapa()
    return render_template('mapacalor.html', labels=result)



def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

if __name__ == '__main__':
    admin = Admin(app, name='Takesi: Corpus', template_mode='bootstrap3')
    admin.add_view(CorpusView(db.DOCS,"Corpus"))
    app.run(debug=True)

