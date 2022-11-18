from operator import truediv
from prometheus_client import Gauge,start_http_server
from elasticsearch import Elasticsearch
import elastic_transport
from time import time,sleep
import re as Regex
import mariadb
import json
import pika
import os
import time
import requests
#TODO: add requests to requirements.txt
#TODO: add publish and consume to and from queue methods
# RabbitMQ
RABBITHOST = os.getenv("RABBITHOST")
RABBITPORT = os.getenv("RABBITPORT")
RABBITUSER = os.getenv("RABBITUSER")
RABBITPASS = os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = os.getenv("RABBITCONSUMEQUEUE")
RABBITPUBLISHQUEUE = os.getenv("RABBITPUBLISHQUEUE")

# Elastic
ELASTICHOST = os.getenv("ELASTICHOST")
ELASTICPORT = os.getenv("ELASTICPORT")
ELASTICUSER = os.getenv("ELASTICUSER")
ELASTICPASS = os.getenv("ELASTICPASS")

# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

#SQLProcessor
SQLPROCESSORRETRIES = os.getenv("SQLPROCESSORRETRIES")
SQLPROCESSORTIMEOUT= os.getenv("SQLPROCESSORTIMEOUT")

# Enum for colors
class bcolors:
    PROCESSING  = '\33[96m'     #CYAN
    OK          = '\033[92m'    #GREEN
    WARNING     = '\033[93m'    #YELLOW
    FAIL        = '\033[91m'    #RED
    GRAY        = '\033[90m'    #GRAY
    RESET       = '\033[0m'     #RESET COLOR

#Class containing the program's logic
class DetailsDownloader:
    #TODO: Preguntar qué es esto 
    __consumerQueue = None
    __publishQueue = None
    __elasticClient = None
    __mariaClient = None
    __currentJob = None
    __currentDoc = None
    __currentDocId = None
    __currentExpression = None
    __currentSqltransform = None
    __time = 0
    __processedGroups = 0
    __totalTimeMetric = None
    __avgTimeMetric = None
    __processedGroupsMetric = None

    def __init__(self):
        self.initQueues()
        self.initMetrics()
        self.connectElastic(
            ELASTICUSER,
            ELASTICPASS,
            ELASTICHOST,
            ELASTICPORT
        )
        self.connectMariadb(
            MARIADBUSER,
            MARIADBPASS,
            MARIADBHOST,
            MARIADBPORT
        )

    # Simple method used to connect to an elasticsearch database
    def connectElastic(self,user,password,host,port):
        self.__elasticClient = Elasticsearch(
            host+":"+port,
            basic_auth=(user,password)
        )
        try:
            self.__elasticClient.info()
            return True
        except elastic_transport.ConnectionError:
            # We raise an exception because the process 
            # can't continue without a place to look for jobs
            raise Exception("Error: Couldn't connect to Jobs database")

    # Simple method used to connect to a MariaDB database
    def connectMariadb(self,user,password,host,port):
        try:
            self.__mariaClient = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=int(port),
                database=MARIADBNAME
            )
        except mariadb.OperationalError:
            # We raise an exception because the process 
            # can't continue without a place to get
            # information to publish in elastic
            raise Exception("Error: Couldn't connect to MariaDB database")

    # Method to initialize consuming queue and the publishing queue
    def initQueues(self):
        rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
        rabbitParameters = pika.ConnectionParameters(
            heartbeat=120,
            blocked_connection_timeout=120,
            host=RABBITHOST,
            port=RABBITPORT,
            credentials=rabbitUserPass
        )
        try:
            self.__consumerQueue = pika.BlockingConnection(rabbitParameters).channel()
            self.__publishQueue = pika.BlockingConnection(rabbitParameters).channel()
            self.__consumerQueue.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            # We can't continue without a queue to get data from 
            # and to publish our results
            raise Exception("Error: Couldn't connect to RabbitMQ")
        self.__consumerQueue.queue_declare(queue=RABBITCONSUMEQUEUE)
        self.__publishQueue.queue_declare(queue=RABBITPUBLISHQUEUE)

        self.__consumerQueue.basic_consume(queue=RABBITCONSUMEQUEUE, on_message_callback=self.consume, auto_ack=False)

    def reconnectPublishQueue(self):
        #Creating parameters to rabbit
        rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
        rabbitParameters = pika.ConnectionParameters(
            heartbeat=120,
            blocked_connection_timeout=120,
            host=RABBITHOST,
            port=RABBITPORT,
            credentials=rabbitUserPass
        )
        #Connecting to RABBITMQ
        try:
            self.__publishQueue = pika.BlockingConnection(rabbitParameters).channel()
        except pika.exceptions.AMQPConnectionError as e:
            # We can't continue without a queue to publish our results
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} Couldn't connect to RabbitMQ")
        #Creating queues
        self.__publishQueue.queue_declare(queue=RABBITPUBLISHQUEUE)

    #TODO: change metrics
    # Method to initialize Prometheus metrics
    def initMetrics(self):
        self.__totalTimeMetric = Gauge(
            'sqlprocessor_total_processing_time', 
            'Total amount of time elapsed when processing'
        )
        self.__avgTimeMetric = Gauge(
            'sqlprocessor_avg_processing_time', 
            'Average amount of time elapsed when processing'
        )
        self.__processedGroupsMetric = Gauge(
            'sqlprocessor_number_processed_groups', 
            'Number of Groups process by SQL Processor'
        )
        self.__totalTimeMetric.set(0)
        self.__avgTimeMetric.set(0)
        self.__processedGroupsMetric.set(0)

    #This method sets the group's status and creates a new record in the 
    #history table
    #TODO: corregir error y revisar que los nombres de las clmns del query estén bien
    #TODO: ver como se consigue el identificador del pod
    def startInMariaDB(self, message):
        id_job = message["id_job"]
        grp_number = message["grp_number"]
        try:
            cursor = self.__mariaClient.cursor()
            #Here we'll update the stage and status of the group in mariadb
            cursor.execute("UPDATE groups SET stage=?, status=? WHERE grp_number=? AND id_job=?", 
            ("details-downloader","in-progress",grp_number, id_job))
            #Here we'll create a new record in the history table
            cursor.execute("INSERT INTO history (stage, status, created, end, message, grp_id, component) VALUES (?,?,?,?,?,?,?)", 
            ("details-downloader","in-progress",int(time.time()), 0, "", "pod-id"))
        except mariadb.ProgrammingError:
            # There is the possibility the query fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "error en details downloader \
                failed, document -> " + bcolors.WARNING + self.__currentDoc["grp_number"] + bcolors.RESET
            )
            return True
        return False
    
    #TODO: corregir error
    #This method sets the status of the process to finished in mariaDB
    def endInMariaDB(self, message):
        id_job = message["id_job"]
        grp_number = message["grp_number"]
        try: 
            cursor = self.__mariaClient.cursor()
            cursor.execute("UPDATE history SET status=?, end=? WHERE grp_number=? AND id_job=?", 
            ("completed", int(time.time())))
        except mariadb.ProgrammingError as e:
            # There is the possibility the query fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "details-downloader \
                failed, document -> " + bcolors.WARNING + self.__currentDoc["grp_number"] + bcolors.RESET
            )
            cursor = self.__mariaClient.cursor()
            cursor.execute("UPDATE history SET status=?, end=?, message=? WHERE grp_number=? AND id_job=?", 
            ("error", int(time.time(), str(e), grp_number, id_job)))
            return True
        return False

    #TODO: corregir error y revisar que los nombres de los fields del query estén bien
    #TODO: preguntar que es SQLPROCESSORTIMEOUT
    #TODO: preguntar si el url de medrxiv se pasa por environment variables
    # This method retrieves the group document from elastic with the
    # recieved id_job and grp_number of the queue
    def getFromElastic(self,message):
        success = False
        try:
            for i in range(int(SQLPROCESSORRETRIES)):
                search = self.__elasticClient.search(index="groups",size=1,query={"match" : {"grp_number" : message["grp_number"]}})
                self.__currentDoc = search["hits"]["hits"][0]["_source"]
                self.__currentDocId = search["hits"]["hits"][0]["_id"]
                if("docs" in self.__currentDoc):
                    success = True
                    break
                sleep(int(SQLPROCESSORTIMEOUT))
            if(not success):
                print(
                    bcolors.FAIL + "Error:" + bcolors.RESET + " Group doesn't have docs in it -> " + bcolors.WARNING + "grp_number:" + 
                    message["grp_number"] + bcolors.RESET
                )
                return True
        except IndexError:
            # if we don't find any document, we can't continue
            print(
                bcolors.FAIL + "Error:" + bcolors.RESET + " Didn't find group -> " + bcolors.WARNING + "grp_number:" + 
                message["grp_number"] + bcolors.RESET
            )
            return True
        return False
    
    #This method adds the details retrieved from the api to each document in elasticsearch
    #TODO: fetch details from api
    def addDetails(self, message):
        docs = self.__currentDoc["docs"]
        detailsUrl = "https://api.biorxiv.org/details/medrxiv/"

        try:
            for doc in docs:
                detailsRequest = requests.get(detailsUrl + doc["rel_doi"])
                doc["details"] = detailsRequest.text

        except mariadb.ProgrammingError:
            # There is the possibility the expression fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "root.stages[name=transform].transformation[type=sql_transform].expression \
                failed, document -> " + bcolors.WARNING + self.__currentDoc["grp_number"] + bcolors.RESET
            )
            return True

        self.__currentDoc["docs"] = docs
        self.__elasticClient.index(index="groups",id=self.__currentDocId,document=self.__currentDoc)
        return False
    
