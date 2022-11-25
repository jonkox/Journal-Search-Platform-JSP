from flask import Flask, request, Response
import pyrebase
from flask_cors import CORS
from prometheus_client import Counter, generate_latest, start_http_server
import datetime
from elasticsearch import Elasticsearch
import elastic_transport
import mariadb
import os


#Elasticsearch
ELASTICHOST = os.getenv("ELASTICHOST")
ELASTICPORT = os.getenv("ELASTICPORT")
ELASTICUSER = os.getenv("ELASTICUSER")
ELASTICPASS = os.getenv("ELASTICPASS")
ELASTICINDEX = os.getenv("ELASTICINDEX")

#MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

METRICSPORT = os.getenv("METRICSPORT")

try:
  MariaClient = mariadb.connect(
            host=MARIADBHOST, 
            port= int(MARIADBPORT),
            user=MARIADBUSER, 
            password= MARIADBPASS, 
            database= MARIADBNAME)
except:
    print("Error: Couldn't connect to database Maria")

try:
  ElasticClient = Elasticsearch(
            ELASTICHOST+":"+ELASTICPORT,
            basic_auth=(ELASTICUSER,ELASTICPASS)
        )
except elastic_transport.ConnectionError:
    raise Exception ("Error: Couldn't connect to database Elastic")

#Firebase
configuration = {
  "apiKey": "AIzaSyAQgbFIM6bW6QoRUkkrkUYYFc6NTvx3NlM",
  "authDomain": "tarea2-43a35.firebaseapp.com",
  "databaseURL": "https://tarea2-43a35-default-rtdb.firebaseio.com",
  "projectId": "tarea2-43a35",
  "storageBucket": "tarea2-43a35.appspot.com",
  "messagingSenderId": "888232706185",
  "appId": "1:888232706185:web:6ba2988a7fc46724af4658"
}

api = Flask(__name__)
CORS(api)

fb = pyrebase.initialize_app(configuration)
base = fb.database()

lista2 = []
#Información para las métricas
NumeroDeRequests = Counter('flask_requests','API Numero de requests')
NumeroDeErrores = Counter('flask_errores', 'API Numero de errores en las llamadas')
NumeroDeDocumentos = Counter('flask_documentos', 'API Numero de documentos retornados')
#-------------------------------------------------------------
# Métricas
#-------------------------------------------------------------
'''@api.route('/metrics')
def inicio():
  return generate_latest()'''

#-------------------------------------------------------------
# Añadir job a MariaDB
#-------------------------------------------------------------
@api.route('/InsertarJob',methods=["POST"])
def insertar():
  NumeroDeRequests.inc()
  datos = request.get_json()
  grp = int(datos["cantidad"])
  #Configurar el indice de Elastic
  mappings = {
      "properties": {
        "rel_date": {
          "type": "text"
        },
        "details.jatsxml": {
          "enabled" : False
        }
      }
    }
  
  try:
      ElasticClient.indices.create(index=ELASTICINDEX, mappings=mappings, settings={'mapping':{'ignore_malformed':True}})
  except:
      print("")
  try:
      cur = MariaClient.cursor()
      createTime = datetime.datetime.now()
      try:
          cur.execute("CREATE TABLE jobs (id INT AUTO_INCREMENT PRIMARY KEY, created datetime(1), status VARCHAR(45), end datetime(1), loader VARCHAR(45), grp_size int(1))")
      except:
          print("")
      cur.execute("INSERT INTO jobs (created, status ,end ,loader,grp_size) VALUES (?,?,?,?,?) ",(createTime,'new',0,0,grp))
      MariaClient.commit()
      return "Agregado correctamente"
  except mariadb.Error as error:
    NumeroDeErrores.inc()
    print("Error in query: {}".format(error))
    cur.connection.close()
  return "Hubo un error"

#-------------------------------
# Buscar articulos en elastic 
#-------------------------------
@api.route('/Buscar',methods=["POST"])
def buscar():
  NumeroDeRequests.inc()
  datos = request.get_json()
  query = datos["consulta"]
  docu = {}
  lista = []
  try:
    respuesta = ElasticClient.search(index=ELASTICINDEX, query={"multi_match" : {"query":query, "fields": 
    ["rel_date","rel_title","rel_site","rel_abs","rel_authors.author_name","rel_authors.author_inst",
    "license","type","category","details.jatsxml"]}},size = 100,source=["rel_title","rel_abs","rel_authors"])
    cantidad = respuesta['hits']['total']['value']
    if cantidad >= 100:
      NumeroDeDocumentos.inc(100)
    else:
      NumeroDeDocumentos.inc(cantidad)
    base.child("articulos").remove()
    for j in respuesta['hits']['hits']:
      lista.append(j["_source"])
      docu = {"titulo":j["_source"]["rel_title"],"autores":j["_source"]["rel_authors"], "abstract": j["_source"]["rel_abs"]}
      lista2.append(docu)
  except:
    NumeroDeErrores.inc()
  return lista

#-----------------------------------------------------------
# Mostrar detalles de un articulo encontrado en la busqueda
#-----------------------------------------------------------
@api.route('/Detalles',methods=["POST"])
def detalles():
  NumeroDeRequests.inc()
  datos = request.get_json()
  titulo = datos["titulo"]
  tipo = datos["tipo"]
  try:
    if tipo == "abstract":
      for j in lista2:
        if j["titulo"]== titulo:
          return j["abstract"]
    else:
        for j in lista2:
          if j["titulo"]== titulo:
            listaAutores = j["autores"]
            return listaAutores
  except:
    NumeroDeErrores.inc()
  return "Error"

#------------------------------------------------------------------------
# Mostrar los detalles de un articulo guardado en la lista de "me gusta"
#-------------------------------------------------------------------------
@api.route('/DetallesLike',methods=["POST"])
def detallesLike():
  NumeroDeRequests.inc()
  datos = request.get_json()
  uid = datos["uid"]
  titulo = datos["titulo"]
  tipo = datos["tipo"]
  try:
    uidArticulo = list(base.child("likes").child(uid).order_by_child("titulo").equal_to(titulo).get().val().keys())[0] 
    if tipo == "abstract":
      abstract = base.child("likes").child(uid).child(uidArticulo).child("abstract").get().val()
      return abstract
    else:
      listaAutores = base.child("likes").child(uid).child(uidArticulo).child("autores").get().val()
      return listaAutores
  except:
    NumeroDeErrores.inc()
  return "Error"

#------------------------------------
# Darle me gusta a un articulo
#-----------------------------------
@api.route('/Like',methods=["POST"])
def like():
  NumeroDeRequests.inc()
  datos = request.get_json()
  uid = datos["uid"]
  titulo = datos["titulo"]
  autores = datos["autores"]
  abstract =  datos["abstract"]
  try:
    uidArticulo = list(base.child("likes").child(uid).order_by_child("titulo").equal_to(titulo).get().val().keys())[0]
    return "Artículo ya está guardado"
  except:
    docu = {"autores": autores, "titulo":titulo, "abstract": abstract}
    base.child("likes").child(uid).push(docu)
  return "Guardado correctamente"

#------------------------------
# Desplegar lista de articulos 
#-----------------------------
@api.route('/ListaLikes',methods=["POST"])
def listaLikes():
  NumeroDeRequests.inc()
  datos = request.get_json()
  uid = datos["uid"]
  try:
    resp = base.child("likes").child(uid).order_by_child("titulo").get().val()
    listaT = list(resp.values())
    return listaT
  except:
    print("")
  return "No hay articulos guardados"

if __name__ == '__main__':
  start_http_server(int(METRICSPORT))
  api.run(debug=False,port=5000)
