# -*- coding: utf-8 -*-

import pymongo
import mongodb
import Documento
import settings as set
from Utils import utilidades
from bson.objectid import ObjectId
from flask import Flask, redirect, request
from flask import render_template, jsonify
from nltk.corpus import stopwords
from flask_admin import Admin
import flask_admin as admin
from wtforms import form, fields
from flask_admin.form import Select2Widget
from flask_admin.contrib.pymongo import ModelView, filters
from flask_admin.model.fields import InlineFormField, InlineFieldList
from bson.objectid import ObjectId
from bson.son import SON


def busqueda_indices(tags):
    #MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
    indices=db.INDEX
    list=indices.find({"tag_vocab" : { '$in': tags}}, projection={"id_doc":1,"_id":0})
    result=[]
    for record in list:
            result.append(record)
    return result

def busqueda_resp(pregunta):

    #MONGODB_URI = 'mongodb://takesibatch:takesi2015@ds053439.mongolab.com:53439/docs'
    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    #db.DOCS.createIndex({"tags_vocab":"text", "texto": "text", "nombre": "text", "tags":"text"},{"name":"indice", "weights":{"tags_vocab":4, "texto":2, "nombre": 3, "tags":5}})
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
    # test = fields.TextField('Test')


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

@app.route('/doc/<id>')
def show_doc(id):

    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    results=DOC.find({"_id": ObjectId(id)}, {"texto" :1,"_id":0})
    return render_template('texto.html', results=results)

@app.route('/stats/')
def estadisticas():

    client = pymongo.MongoClient(set.MONGODB_URI)
    db = client.docs
    DOC=db.DOCS
    pipeline = [{"$unwind": "$tag_vocab"},{"$group": {"_id": "$tag_vocab", "count": {"$sum": 1}}},{"$sort": SON([("count", -1), ("_id", -1)])}]
    data=(list(DOC.aggregate(pipeline)))
    return jsonify(output=data)

@app.route('/busqueda', methods=['POST'])
def busqueda():
    pregunta=request.form['text']
    vocab=bw.LeeBagWords()
    pregunta_2=utilidades.SinStopwords(pregunta)
    pregunta_2=utilidades.Stemming(pregunta_2)
    writer.inserta_pregunta(pregunta_2)
    respuestas=busqueda_resp(pregunta_2)
    docs=respuestas.clone()
    text=[]
    for d in docs:
        doc=Documento.Document(d)
        text.append(doc.similaridad(pregunta_2))
    text=sorted(text, key=lambda text: text[1], reverse=True)
    t = tuple(x[0] for x in text)
    #text=reader.localizar(pregunta)

    return render_template('resultados.html',  resps=respuestas, entries=t, question=pregunta)

@app.route('/graph/')
def home():
    """ Simply serve our chart page """
    return render_template('chart1.html')

if __name__ == '__main__':
    admin = Admin(app, name='Takesi: Corpus', template_mode='bootstrap3')
    admin.add_view(CorpusView(db.DOCS,"Corpus"))
    app.run(debug=True)