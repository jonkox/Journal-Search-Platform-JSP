import unittest
from elasticsearch import Elasticsearch
import mariadb
import datetime
import pyrebase

class TestApi(unittest.TestCase):

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

    fb = pyrebase.initialize_app(configuration)
    base = fb.database()

    MariaClient = mariadb.connect(
            host='localhost', 
            port= 32100,
            user='root', 
            password= "SlVQOxsghQ", 
            database= 'pruebaUnitaria')
    cur = MariaClient.cursor()

    ElasticClient = Elasticsearch(
            "http://localhost:53608/",
            basic_auth=("elastic","Gu6cigeirVvLXZAa")
        )

    response = ""
    lista2 = []

    def test_insertar_job_Ok(self):
        peticion = {"cantidad": 7}
        try:
            createTime = datetime.datetime.now()
            try:
                self.cur.execute("CREATE TABLE jobs (id INT AUTO_INCREMENT PRIMARY KEY, created datetime(1), status VARCHAR(45), end datetime(1), loader VARCHAR(45), grp_size int(1))")
            except:
                print("")
            self.cur.execute("INSERT INTO jobs (created, status ,end ,loader,grp_size) VALUES (?,?,?,?,?) ",(createTime,'new',0,0,peticion["cantidad"]))
            self.MariaClient.commit()
            response = "Exito"
        except mariadb.Error as error:
            print("Error in query: {}".format(error))
            response = "Error"

        self.assertEqual(response,"Exito")


    def test_insertar_job_FAIL(self):
        peticion = {"cantidad": ""}    
        createTime = datetime.datetime.now()

        if peticion["cantidad"] == "" :
            response = "Error"
        else:
            try:
                try:
                    self.cur.execute("CREATE TABLE jobs (id INT AUTO_INCREMENT PRIMARY KEY, created datetime(1), status VARCHAR(45), end datetime(1), loader VARCHAR(45), grp_size int(1))")
                except:
                    print("")
                self.cur.execute("INSERT INTO jobs (created, status ,end ,loader,grp_size) VALUES (?,?,?,?,?) ",(createTime,'new',0,0,peticion["cantidad"]))
                self.MariaClient.commit()
                response = "Exito"
            except mariadb.Error as error:
                print("Error in query: {}".format(error))
                response = "Error"
                self.cur.connection.close()
        self.assertEqual(response,"Error")


    def test_buscar_OK(self):
        peticion = {"consulta": "covid"}   
        query = peticion["consulta"]
        lista = []
        docu = {}

        if peticion["consulta"] == "" :
            response = "Error"
        else:
            try:
                respuesta = self.ElasticClient.search(index="articulos", query={"multi_match" : {"query":query, "fields": 
                ["rel_date","rel_title","rel_site","rel_abs","rel_authors.author_name","rel_authors.author_inst",
                "license","type","category","details.jatsxml"]}},size = 100)
                for j in respuesta['hits']['hits']:
                    lista.append(j["_source"])
                    docu = {"titulo":j["_source"]["rel_title"],"autores":j["_source"]["rel_authors"], "abstract": j["_source"]["rel_abs"]}
                    self.lista2.append(docu)
                    response =  "Correcto"
            except:
                response =  "Error"
        self.assertEqual(response,"Correcto")

    def test_buscar_FAIL(self):
        peticion = {"consulta": ""}   
        query = peticion["consulta"]
        lista = []
        docu = {}

        if peticion["consulta"] == "" :
            response = "Error"
        else:
            try:
                respuesta = self.ElasticClient.search(index="articulos", query={"multi_match" : {"query":query, "fields": 
                ["rel_date","rel_title","rel_site","rel_abs","rel_authors.author_name","rel_authors.author_inst",
                "license","type","category","details.jatsxml"]}},size = 100)
                for j in respuesta['hits']['hits']:
                    lista.append(j["_source"])
                    docu = {"titulo":j["_source"]["rel_title"],"autores":j["_source"]["rel_authors"], "abstract": j["_source"]["rel_abs"]}
                    self.lista2.append(docu)
                    response =  "Correcto"
            except:
                response =  "Error"
        self.assertEqual(response,"Error")


    def test_detalles_OK(self):
        peticion = {"titulo":"titulo 5", "tipo": "abstract"}
        titulo = peticion["titulo"]
        tipo = peticion["tipo"]
        resultT = ""
        resultA = []
        try:
            if tipo == "abstract":
                for j in self.lista2:
                    if j["titulo"]== titulo:
                        resultT = j["titulo"]
                        
            else:
                for j in self.lista2:
                    if j["titulo"]== titulo:
                        resultA = j["autores"]
        except:
            response = "Error"
        if resultT == titulo:
            response = "Correcto"
        elif resultA != []:
            response = "Correcto" 
        else:
            response = "Error"
        self.assertEqual(response,"Correcto")

    def test_detalles_FAIL(self):
        peticion = {"titulo":"titulo prueba", "tipo": "abstract"}
        titulo = peticion["titulo"]
        tipo = peticion["tipo"]
        resultT = ""
        resultA = []
        try:
            if tipo == "abstract":
                for j in self.lista2:
                    if j["titulo"]== titulo:
                        resultT = j["titulo"]
                        
            else:
                for j in self.lista2:
                    if j["titulo"]== titulo:
                        resultA = j["autores"]
        except:
            response = "Error"
        if resultT == titulo:
            response = "Correcto"
        elif resultA != []:
            response = "Correcto" 
        else:
            response = "Error"
        self.assertEqual(response,"Error")
    
    def test_detalles_like_OK(self):
        peticion = {"uid":"8gSeE6dfxAU36k59J4XqDR41BVs2", "titulo":"titulo 5", "tipo": "abstract"}
        uid = peticion["uid"]
        titulo = peticion["titulo"]
        tipo = peticion["tipo"]
        try:
            uidArticulo = list(self.base.child("likes").child(uid).order_by_child("titulo").equal_to(titulo).get().val().keys())[0] 
            if tipo == "abstract":
                abstract = self.base.child("likes").child(uid).child(uidArticulo).child("abstract").get().val()
            else:
                listaAutores = self.base.child("likes").child(uid).child(uidArticulo).child("autores").get().val()    
            response = "Correcto"  
        except:
            response = "Error"

        self.assertEqual(response,"Correcto")

    def test_detalles_like_FAIL(self):
        peticion = {"uid":"8gSeE6dfxAU36k59J4XqDR41BVs2", "titulo":"titulo prueba", "tipo": "abstract"}
        uid = peticion["uid"]
        titulo = peticion["titulo"]
        tipo = peticion["tipo"]
        try:
            uidArticulo = list(self.base.child("likes").child(uid).order_by_child("titulo").equal_to(titulo).get().val().keys())[0] 
            if tipo == "abstract":
                abstract = self.base.child("likes").child(uid).child(uidArticulo).child("abstract").get().val()
            else:
                listaAutores = self.base.child("likes").child(uid).child(uidArticulo).child("autores").get().val()    
            response = "Correcto"  
        except:
            response = "Error"

        self.assertEqual(response,"Error")

    def test_like_OK(self):
        peticion = {"uid":"8gSeE6dfxAU36k59J4XqDR41BVs2", "titulo":"titulo 108", "autores": [], "abstract":"prueba"}
        uid = peticion["uid"]
        titulo = peticion["titulo"]
        autores = peticion["autores"]
        abstract =  peticion["abstract"]
        try:
            uidArticulo = list(self.base.child("likes").child(uid).order_by_child("titulo").equal_to(titulo).get().val().keys())[0]
            response = "Articulo ya guardado"
        except:
            docu = {"autores": autores, "titulo":titulo, "abstract": abstract}
            self.base.child("likes").child(uid).push(docu)
            response = "Guardado correctamente"
        self.assertEqual(response,"Guardado correctamente")
    
    def test_like_FAIL(self):
        peticion = {"uid":"8gSeE6dfxAU36k59J4XqDR41BVs2", "titulo":"titulo 99", "autores": [], "abstract":"prueba"}
        uid = peticion["uid"]
        titulo = peticion["titulo"]
        autores = peticion["autores"]
        abstract =  peticion["abstract"]
        try:
            uidArticulo = list(self.base.child("likes").child(uid).order_by_child("titulo").equal_to(titulo).get().val().keys())[0]
            response = "Articulo ya guardado"
        except:
            docu = {"autores": autores, "titulo":titulo, "abstract": abstract}
            self.base.child("likes").child(uid).push(docu)
            response = "Guardado correctamente"

        self.assertEqual(response,"Articulo ya guardado")


    def test_listaLikes_Ok(self):
        peticion = {"uid":"8gSeE6dfxAU36k59J4XqDR41BVs2"}
        uid = peticion["uid"]
        try:
            resp = self.base.child("likes").child(uid).order_by_child("titulo").get().val()
            listaT = list(resp.values())
            response = "Correcto"
        except:
            response = "Lista vacia"

        self.assertEqual(response,"Correcto")

    def test_listaLikes_FAIL(self):
        peticion = {"uid":"KU0nn2U2OKUpnyuy664pGDnKphS2"}
        uid = peticion["uid"]
        try:
            resp = self.base.child("likes").child(uid).order_by_child("titulo").get().val()
            listaT = list(resp.values())
            response = "Correcto"
        except:
            response = "Lista vacia"

        self.assertEqual(response,"Lista vacia")

if __name__ == '__main__':
	unittest.main()
