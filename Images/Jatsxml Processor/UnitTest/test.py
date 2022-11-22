from elasticsearch import Elasticsearch
import elastic_transport
import mariadb
import json
import pika
import os

ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "IzcPIZsyMsLk6E5s" #os.getenv("ELASTICPASS")

MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")
MARIADBHOST = "localhost" #os.getenv("MARIADBHOST")
MARIADBPORT = "32100" #os.getenv("MARIADBPORT")
MARIADBUSER = "root" #os.getenv("MARIADBUSER")
MARIADBPASS = "jtGlurMZin" #os.getenv("MARIADBPASS")

# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "KzJwjgdHFZV2p5CY" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "details-downloader" #os.getenv("RABBITQUEUENAME")

elasticClient = Elasticsearch(
    ELASTICHOST +":"+ELASTICPORT,
    basic_auth=(ELASTICUSER,ELASTICPASS)
)
try:
    elasticClient.info()
    if(not (elasticClient.indices.exists(index=["groups"]))):
        elasticClient.indices.create(index="groups")
except elastic_transport.ConnectionError:
    # We raise an exception because the process 
    # can't continue without a place to look for jobs
    raise Exception("Error: Couldn't connect database")

try:
    mariaClient = mariadb.connect(
        user=MARIADBUSER,
        password=MARIADBPASS,
        host=MARIADBHOST,
        port=int(MARIADBPORT),
        database=MARIADBNAME
    )
except mariadb.OperationalError:
    # We raise an exception because the process 
    # can't continue without a place to get
    # information to publish in elastic
    raise Exception("Error: Couldn't connect to MariaDB database")

rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
rabbitParameters = pika.ConnectionParameters(
    heartbeat=120,
    blocked_connection_timeout=120,
    host=RABBITHOST,
    port=RABBITPORT,
    credentials=rabbitUserPass
)

try:
    consumerQueue = pika.BlockingConnection(rabbitParameters).channel()
except pika.exceptions.AMQPConnectionError:
    # We can't continue without a queue to get data from 
    # and to publish our results
    raise Exception("Error: Couldn't connect to RabbitMQ")
consumerQueue.queue_declare(queue=RABBITCONSUMEQUEUE)


with open(os.path.join(os.path.dirname(__file__),"prueba.json")) as archivo:
    group = json.load(archivo)


search = elasticClient.search(index="groups",size=20)

if(search["hits"]["total"]["value"] == 0):
    elasticClient.index(index="groups", document=group,refresh='wait_for')

cursor = mariaClient.cursor()

cursor.execute("delete from history where true = true")
cursor.execute("delete from `groups` where true = true")
cursor.execute("delete from jobs where true = true")


cursor.execute('INSERT INTO jobs (id,created,status,end,loader,grp_size) VALUES (1,NOW(),"new",NULL,"loader_23i0sk2",5)')
cursor.execute('INSERT INTO `groups` (id,id_job,created,`end`,stage,grp_number,`status`,`offset`) VALUES (232,1,NOW(),NULL,"details downloader",3,"In-progress",20)')

mariaClient.commit()

message = {
    "id_job": "1",
    "grp_number": "3"
}

consumerQueue.queue_purge(queue=RABBITCONSUMEQUEUE)
consumerQueue.basic_publish(routing_key=RABBITCONSUMEQUEUE, body=json.dumps(message), exchange='')



