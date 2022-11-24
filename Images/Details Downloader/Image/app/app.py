from operator import truediv
from prometheus_client import Gauge,Counter,start_http_server
from elasticsearch import Elasticsearch
import elastic_transport
from time import time,sleep
import mariadb
import json
import pika
import os
import time
import requests


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

#jatsxml
PODNAME = os.getenv("HOSTNAME")
APIURL = os.getenv("APIURL")
METRICSPORT = os.getenv("METRICSPORT")

"""#Test values
# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "KzJwjgdHFZV2p5CY" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "downloader" #os.getenv("RABBITQUEUENAME")
RABBITPUBLISHQUEUE = "publish" #os.getenv("RABBITPUBLISHQUEUE")

# Elastic
ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "IzcPIZsyMsLk6E5s" #os.getenv("ELASTICPASS")
ELASTICINDEX = "registries" #os.getenv("ELASTICINDEX")
# MariaDB
MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")
MARIADBHOST = "localhost" #os.getenv("MARIADBHOST")
MARIADBPORT = "32100" #os.getenv("MARIADBPORT")
MARIADBUSER = "root" #os.getenv("MARIADBUSER")
MARIADBPASS = "jtGlurMZin" #os.getenv("MARIADBPASS")

#details
PODNAME = "podname" #os.getenv("HOSTNAME")
APIURL = "https://api.biorxiv.org/" #os.getenv("APIURL")"""


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
    __consumerQueue = None
    __publishQueue = None
    __elasticClient = None
    __mariaClient = None
    __currentGroup = None
    __currentGroupId = None
    __currentHistoryId = None
    __currentMessage = None
    __historyMessage = ""

    __processedDetails = None
    __notProcessedDetails = None
    __processedGroups = None
    __errorCount = None
    __timeProcessingGroup = Gauge(
            'detailsdownloader_processing_time_per_group', 
            'Total amount of time elapsed when processing'
        )
    

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
            if(not (self.__elasticClient.indices.exists(index=["groups"]))):
                self.__elasticClient.indices.create(index="groups")
            return True
        except elastic_transport.ConnectionError:
            # We raise an exception because the process can't continue
            # without a place to look for groups and publish
            raise Exception("Error: Couldn't connect to Elasticsearch database")

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
            # can't continue without a place to publish
            # history registries, and modify jobs and groups
            raise Exception("Error: Couldn't connect to MariaDB database")

        # We try to create tables so they exists when the process starts
        jobsTable = "CREATE TABLE IF NOT EXISTS jobs ( \
                            id INT NOT NULL AUTO_INCREMENT, \
                            created DATETIME, \
                            status VARCHAR(45), \
                            end DATETIME, \
                            loader VARCHAR(45), \
                            grp_size INT, \
                            PRIMARY KEY (id) \
                        )"

        groupsTable = "CREATE TABLE IF NOT EXISTS groups ( \
                            id INT NOT NULL AUTO_INCREMENT, \
                            id_job INT NOT NULL, \
                            created DATETIME, \
                            end DATETIME, \
                            stage VARCHAR(45), \
                            grp_number INT, \
                            status VARCHAR(45), \
                            `offset` INT, \
                            PRIMARY KEY (id), \
                            FOREIGN KEY (id_job) REFERENCES jobs (id) \
                        )"

        historyTable = "CREATE TABLE IF NOT EXISTS history ( \
                            id INT NOT NULL AUTO_INCREMENT, \
                            component VARCHAR(60), \
                            status VARCHAR(45), \
                            created DATETIME, \
                            end DATETIME, \
                            message TEXT, \
                            grp_id INT NOT NULL, \
                            stage VARCHAR(45), \
                            PRIMARY KEY (id), \
                            FOREIGN KEY (grp_id) REFERENCES groups (id) \
                        )"

        cursor = self.__mariaClient.cursor()
        cursor.execute(jobsTable)
        cursor.execute(groupsTable)
        cursor.execute(historyTable)
        cursor.execute("SET GLOBAL time_zone = '-6:00'")
        self.__mariaClient.commit()

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
            print(f"{bcolors.FAIL}Error:{bcolors.RESET} Couldn't connect to RabbitMQ")
        #Creating queues
        self.__publishQueue.queue_declare(queue=RABBITPUBLISHQUEUE)

    #TODO: change metrics
    # Method to initialize Prometheus metrics
    def initMetrics(self):
        self.__processedDetails = Counter(
            'detailsdownloader_processed_details',
            'Number of times a jatsxml has been processed (exists)'
        )

        self.__notProcessedDetails = Counter(
            'detailsdownloader_not_processed_details',
            'Number of times a jatsxml hasn\'t been processed (doesn\'t exists)'
        )

        self.__processedGroups = Counter(
            'detailsdownloader_processed_groups',
            'Number of processed groups'
        )

        self.__errorCount = Counter(
            'detailsdownloader_error_count',
            'Number of errors'
        )

    #This method sets the group's status and creates a new record in the 
    #history table
    #TODO: corregir error y revisar que los nombres de las clmns del query estén bien
    #TODO: ver como se consigue el identificador del pod
    def startInMariaDB(self):
        id_job = self.__currentMessage["id_job"]
        grp_number = self.__currentMessage["grp_number"]
        try:
            cursor = self.__mariaClient.cursor()
            #Here we'll update the stage and status of the group in mariadb
            cursor.execute("UPDATE groups SET stage=?, status=?, id=last_insert_id(id) WHERE grp_number=? AND id_job=?", 
            ("details-downloader","in-progress",grp_number, id_job))

            grp_id = cursor.lastrowid

            #Here we'll create a new record in the history table
            cursor.execute("INSERT INTO history (stage, status, created, end, message, grp_id, component) VALUES (?,?,NOW(),NULL,?,?,?)", 
            ("details-downloader", "in-progress", "", grp_id, PODNAME))

            self.__currentHistoryId = cursor.lastrowid
            self.__mariaClient.commit()
        except mariadb.ProgrammingError:
            # There is the possibility the query fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "Couldn't update group nor insert in history table " +
                "document -> " + bcolors.WARNING + self.__currentMessage + bcolors.RESET
            )
            self.__historyMessage = "Error in startInMariaDB() function: Couldn't update group nor insert in history table"
            self.__errorCount.inc()
            return True
        return False
    
    #This method sets the status of the process to finished in mariaDB
    def endInMariaDB(self,result):
        try:
            if result:
                status = "Error"
            else:
                status = "Completed"

            cursor = self.__mariaClient.cursor()
            cursor.execute("UPDATE history SET status=?, message=?, end=NOW() WHERE id = ?", 
            (status,self.__historyMessage,self.__currentHistoryId))

            self.__mariaClient.commit()
        except mariadb.ProgrammingError:
            # There is the possibility the query fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "Couldn't update history table " +
                "document -> " + bcolors.WARNING + self.__currentMessage + bcolors.RESET
            )
            self.__errorCount.inc()
            return True
        return False

    #TODO: revisar que los nombres de los fields del query estén bien
    #TODO: preguntar para que sirve SQLPROCESSORTIMEOUT
    #TODO: preguntar si el url de medrxiv se pasa por environment variables
    # This method retrieves the group document from elastic with the
    # recieved id_job and grp_number of the queue
    def getGroupFromElastic(self):
        try:
            search = self.__elasticClient.search(
                index="groups",size=1,
                query={
                    "bool": { 
                        "must": [ 
                            { "match": { 
                                "id_job": self.__currentMessage["id_job"] 
                                } 
                            }, 
                            { "match": { 
                                "grp_number": self.__currentMessage["grp_number"] 
                                } 
                            } 
                        ] 
                    } 
                }
            )
            self.__currentGroup = search["hits"]["hits"][0]["_source"]
            self.__currentGroupId = search["hits"]["hits"][0]["_id"]
        except IndexError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} Didn\'t find group' +
                f' document -> {bcolors.WARNING}{self.__currentMessage}{bcolors.RESET}'
            )
            self.__historyMessage = "Error in getGroupFromElastic() function: Group was't found in Elasticsearch"
            self.__errorCount.inc()
            return True
        
        print(f'{bcolors.OK}Processing:{bcolors.RESET} success at getting group from elastic' +
            f' document -> {bcolors.GRAY}{self.__currentMessage}{bcolors.RESET}'
        )
        return False
    
    #This method adds the details retrieved from the api to each document in elasticsearch
    #TODO: pass url through env variables
    def addDetails(self):
        docs = self.__currentGroup["docs"]

        try:
            for doc in docs:
                if("rel_site" not in doc or "rel_doi" not in doc):
                    self.__notProcessedDetails.inc()
                    continue
                detailsRequest = requests.get(APIURL + "details/" + doc["rel_site"].lower() + "/" + doc["rel_doi"])
                details = json.loads(detailsRequest.content)
                if("collection" not in details):
                    self.__notProcessedDetails.inc()
                    continue
                if(len(details["collection"]) <= 0):
                    self.__notProcessedDetails.inc()
                    continue
                doc["details"] = details["collection"][0]
                self.__processedDetails.inc()

        except:
            # There is the possibility the expression fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "Error while trying to get details" +
                " document -> " + bcolors.WARNING + self.__currentMessage + bcolors.RESET
            )
            self.__historyMessage = "Error in addDetails() function: Error while trying to get details"
            self.__errorCount.inc()
            return True

        self.__currentGroup["docs"] = docs
        self.__elasticClient.index(index="groups",id=self.__currentGroupId,document=self.__currentGroup, refresh='wait_for')
        return False
    
    #Publish to the queue the new message
    def produce(self, message):
        try:
            self.__publishQueue.basic_publish(routing_key=RABBITPUBLISHQUEUE, body=message, exchange='')
        except pika.exceptions.StreamLostError:
            print(f"{bcolors.FAIL}Error:{bcolors.RESET} connection lost, reconnecting... ")
            self.reconnectPublishQueue()
            self.produce(message)

    @__timeProcessingGroup.time()
    # Method that has all the processing
    def processing(self):
        if ("id_job" not in self.__currentMessage or "grp_number" not in self.__currentMessage):
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} invalid message obtain from queue')
            self.__errorCount.inc()
            return True
        
        if(self.startInMariaDB()):
            return True

        if(self.getGroupFromElastic()):
            return True
        
        if(self.addDetails()):
            return True

        self.produce(json.dumps(self.__currentMessage))

        return False

    # Method used as callback for the consume
    def consume(self, ch, method, properties, msg):
        self.__currentMessage = json.loads(msg)

        print(f'{bcolors.OK}Message Receive:{bcolors.RESET} Starting Process -> {bcolors.GRAY}{str(self.__currentMessage)}')

        result = self.processing()
        if(not result and self.__historyMessage == ""):
            self.__historyMessage = "succesful process"
        self.endInMariaDB(result)
        self.__historyMessage = ""
    
        print(f'{bcolors.OK}Group finished:{bcolors.RESET} ->' +
            f' {bcolors.GRAY}{self.__currentMessage}{bcolors.RESET}'
        )
        self.__processedGroups.inc()
        ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

    def startProcess(self):
        start_http_server(int(METRICSPORT))
        self.__consumerQueue.start_consuming()

downloader = DetailsDownloader()
downloader.startProcess()