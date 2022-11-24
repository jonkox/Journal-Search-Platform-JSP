import json
import elasticsearch
import elastic_transport
import mysql.connector

from urllib.request import urlopen
from elasticsearch import Elasticsearch

ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "m2Hl6qYVLMNFDfdZ" #cambiar contraseña si se desinstala #os.getenv("ELASTICPASS")
ELASTICINDEX = "groups"

MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "9xyqnMJvfy"

# ---------- CONNECT TO ES -------------
try:
    ElasticClient = Elasticsearch(
            ELASTICHOST+":"+ELASTICPORT,
            basic_auth=(ELASTICUSER,ELASTICPASS)
        )
except elastic_transport.ConnectionError:
    raise Exception ("Error: Couldn't connect to ElasticSearch")

# ----------- CONNECT TO MARIADB ---------  
try:
    mariaClient = mysql.connector.connect(
        host=MARIADBHOST, 
        port= MARIADBPORT,
        user=MARIADBUSER, 
        password= MARIADBPASS, 
        database= MARIADBNAME)
    # Get Cursor
    mariadbCursor = mariaClient.cursor(prepared = True)
except:
    print("Error: Couldn't connect to MariaDB") 

url = "https://api.biorxiv.org/covid19/0"
processed_groups = 1

def descargar_docs(url, id_job, processed_groups):
    # Get responde from bioRxiv API
    urlResult = urlopen(url)

    # Get JSON with API response
    data_json = json.loads(urlResult.read())

    collection = data_json["collection"]

    # Get group size 
    grp_size_query = """SELECT grp_size from jobs WHERE id = %s"""
    mariadbCursor.execute(grp_size_query, (id_job,))
    grp_size = int(mariadbCursor.fetchone()[0])

    previous_job_id = processed_groups - 1

    print(processed_groups - 1)
    print(processed_groups * grp_size)
    docs = []

    for i in range (previous_job_id * grp_size, processed_groups * grp_size):
        docs.append(collection[i])

    # for i in range(0, len(docs)):
    #     print(docs[i])
    #     print("")

    publicar_docs(docs)

def publicar_docs(docs):
    for doc in docs:
        publishingResult = ElasticClient.index(
            index = ELASTICINDEX,
            document = doc,
        )
    
descargar_docs(url, 0, processed_groups)