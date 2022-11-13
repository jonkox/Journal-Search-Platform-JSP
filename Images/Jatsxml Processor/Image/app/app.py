from prometheus_client import Gauge,start_http_server
from elasticsearch import Elasticsearch
from time import time
from xml import parsers

import elastic_transport
import xmltodict
import requests
import mariadb
import json
import pika

import os

"""# RabbitMQ
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
MARIADBPASS = os.getenv("MARIADBPASS")"""


# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "TsQYlY3Af6FJ92vW" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "details-downloader" #os.getenv("RABBITQUEUENAME")
RABBITPUBLISHQUEUE = "jatsxml" #os.getenv("RABBITQUEUENAME")

# Elastic
ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "ClDciEHZmjEQvyEg" #os.getenv("ELASTICPASS")

# MariaDB
MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")
MARIADBHOST = "localhost" #os.getenv("MARIADBHOST")
MARIADBPORT = "32100" #os.getenv("MARIADBPORT")
MARIADBUSER = "root" #os.getenv("MARIADBUSER")
MARIADBPASS = "7OBEI1LHV9" #os.getenv("MARIADBPASS")

# Enum for colors
class bcolors:
    PROCESSING  = '\33[96m'     #CYAN
    OK          = '\033[92m'    #GREEN
    WARNING     = '\033[93m'    #YELLOW
    FAIL        = '\033[91m'    #RED
    GRAY        = '\033[90m'    #GRAY
    RESET       = '\033[0m'     #RESET COLOR

# Class containing the programs logic
class JatsxmlProcessor:
    __consumerQueue = None
    __publishQueue = None
    __elasticClient = None
    __mariaClient = None
    __currentJob = None
    __currentJatsLink = None
    __currentObtainJatsxml = None

    def __init__(self):
        """self.initQueues()
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
        )"""

        #self.connectElastic()

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

    #Publish to the queue the new message
    def produce(self, message):
        try:
            self.__publishQueue.basic_publish(routing_key=RABBITPUBLISHQUEUE, body=message, exchange='')
        except pika.exceptions.StreamLostError:
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} connection lost, reconnecting... ")
            self.reconnectPublishQueue()
            self.produce(message)

    def getJatsxml(self):
        self.__currentJatsLink = "https://www.medrxiv.org/content/early/2022/11/08/2022.11.07.22282054.source.xml" # for testing

        try:
            jats = requests.get(self.__currentJatsLink)
        except requests.exceptions.MissingSchema:
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} jatsxml url is invalid")
            return True

        try:
            self.__currentObtainJatsxml=xmltodict.parse(jats.content)
        except parsers.expat.ExpatError:
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} invalid jatsxml format")
            return True

        print(json.dumps(self.__currentObtainJatsxml,indent=6))

        print(f"{bcolors.OK} Processing: {bcolors.RESET} success at getting Jatsxml")
        return False

    # Method used as callback for the consume
    def consume(self, ch, method, properties, msg):
        
        startTime = time()
        message = json.loads(msg)

        ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

    def startProcess(self):
        start_http_server(6941)
        self.__consumerQueue.start_consuming()

prueba = JatsxmlProcessor()