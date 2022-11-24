from prometheus_client import Counter,Gauge,start_http_server
from elasticsearch import Elasticsearch
from xml import parsers

import elastic_transport
import xmltodict
import requests
import mariadb
import json
import pika

import os

# RabbitMQ
RABBITHOST = os.getenv("RABBITHOST")
RABBITPORT = os.getenv("RABBITPORT")
RABBITUSER = os.getenv("RABBITUSER")
RABBITPASS = os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = os.getenv("RABBITCONSUMEQUEUE")

# Elastic
ELASTICHOST = os.getenv("ELASTICHOST")
ELASTICPORT = os.getenv("ELASTICPORT")
ELASTICUSER = os.getenv("ELASTICUSER")
ELASTICPASS = os.getenv("ELASTICPASS")
ELASTICINDEX = os.getenv("ELASTICINDEX")

# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

#jatsxml
PODNAME = os.getenv("HOSTNAME")
METRICSPORT = os.getenv("METRICSPORT")


"""# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "Aql2pHggW47VY67N" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "details-downloader" #os.getenv("RABBITQUEUENAME")

# Elastic
ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "B8DbB6rA1FisP8ZD" #os.getenv("ELASTICPASS")
ELASTICINDEX = "registries" #os.getenv("ELASTICINDEX")

# MariaDB
MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")
MARIADBHOST = "localhost" #os.getenv("MARIADBHOST")
MARIADBPORT = "32100" #os.getenv("MARIADBPORT")
MARIADBUSER = "root" #os.getenv("MARIADBUSER")
MARIADBPASS = "O0wP5VaZ01" #os.getenv("MARIADBPASS")

#jatsxml
PODNAME = "placeholderPodName" #os.getenv("HOSTNAME")"""

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
    __elasticClient = None
    __mariaClient = None
    __currentMessage = None
    __currentGroup = None
    __currentGroupId = None
    __historyMessage = ""
    __historyId = None

    __processedJatsxml = None
    __notProcessedJatsxml = None
    __processedGroups = None
    __errorCount = None

    __processingTimePerGroup = Gauge(
            'jatsxml_processing_time_per_group', 
            'Time elapsed from processing each group'
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
        self.startProcess()

    # Simple method used to connect to an elasticsearch database
    def connectElastic(self,user,password,host,port):
        self.__elasticClient = Elasticsearch(
            host+":"+port,
            basic_auth=(user,password)
        )
        
        # Mappings to avoid elasticsearch changing data types
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
            self.__elasticClient.info()
            if(not (self.__elasticClient.indices.exists(index=["groups"]))):
                self.__elasticClient.indices.create(index="groups")
            if(not (self.__elasticClient.indices.exists(index=[ELASTICINDEX]))):
                self.__elasticClient.indices.create(index=ELASTICINDEX,mappings=mappings,settings={'mapping':{'ignore_malformed':True}})
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
            self.__consumerQueue.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            # We can't continue without a queue to get data from 
            raise Exception("Error: Couldn't connect to RabbitMQ")
        self.__consumerQueue.queue_declare(queue=RABBITCONSUMEQUEUE)
        self.__consumerQueue.basic_consume(queue=RABBITCONSUMEQUEUE, on_message_callback=self.consume, auto_ack=False)

    # Method to initialize Prometheus metrics
    def initMetrics(self):
        self.__processedJatsxml = Counter(
            'jatsxml_processed_jatsxml',
            'Number of times a jatsxml has been processed (exists)'
        )

        self.__notProcessedJatsxml = Counter(
            'jatsxml_not_processed_jatsxml',
            'Number of times a jatsxml hasn\'t been processed (doesn\'t exists)'
        )

        self.__processedGroups = Counter(
            'jatsxml_processed_groups',
            'Number of processed groups'
        )

        self.__errorCount = Counter(
            'jatsxml_error_count',
            'Number of errors'
        )

    # Method in charge of getting the jatsxml and returning a json equivalent
    def getJatsxml(self,currentJatsLink):
        try:
            jats = requests.get(currentJatsLink)
        except requests.exceptions.MissingSchema:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} jatsxml url is invalid' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "While processing docs, one or more docs didn't get a valid jatsxml json equivalent"
            self.__errorCount.inc()
            return "Failed"

        try:
            currentObtainJatsxml=xmltodict.parse(jats.content)
        except parsers.expat.ExpatError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} invalid jatsxml format' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "While processing docs, one or more docs didn't get a valid jatsxml json equivalent"
            self.__errorCount.inc()
            return "Failed"

        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at getting Jatsxml' +
            f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return currentObtainJatsxml

    # Method in charge of updating the group when first starting the process
    def updateGroup(self):
        cursor = self.__mariaClient.cursor()
        updateQuery = f'UPDATE `groups` \
                        SET stage = \"jatsxml-processor\", \
                        status = \"In-progress\" \
                        WHERE grp_number = {self.__currentMessage["grp_number"]} \
                        AND id_job = {self.__currentMessage["id_job"]}'
        try:
            cursor.execute(updateQuery)
            self.__mariaClient.commit()
        except mariadb.ProgrammingError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t update group table' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "Error in updateGroup() function: Couldn't update group"
            self.__errorCount.inc()
            return True
        
        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at updating group table' +
            f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return False

    # Method in charge of updating the group when finishing a process
    def finishedGroup(self):
        cursor = self.__mariaClient.cursor()
        updateQuery = f'UPDATE `groups` \
                        SET status = \"Completed\", \
                        end = NOW() \
                        WHERE grp_number = {self.__currentMessage["grp_number"]} \
                        AND id_job = {self.__currentMessage["id_job"]}'

        try:
            cursor.execute(updateQuery)
            self.__mariaClient.commit()
        except mariadb.ProgrammingError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t update group table' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "Error in finishedGroup() function: Couldn't update group table"
            self.__errorCount.inc()
            return True
        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at updating group table' +
            f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return False

    # Method in charge of updating the job if it has been completed
    def finishedJob(self):
        cursor = self.__mariaClient.cursor()
        checkQuery = f'SELECT count(1) FROM `groups` where id_job = {self.__currentMessage["id_job"]} AND status = "in-progress"'

        try:
            cursor.execute(checkQuery)
        except mariadb.ProgrammingError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t read jobs table' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "Error in finishedJob() function: Couldn't read jobs table"
            self.__errorCount.inc()
            return True
        
        try:
            currentInprocessGroups = cursor.fetchone()[0]
        except IndexError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} didn\'t get a valid response from jobs table' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "Error in finishedJob() function: Didn't get a valid response from jobs table"
            self.__errorCount.inc()
            return True
        
        if(currentInprocessGroups <= 0):
            updateJobQuery = f'UPDATE jobs \
                               SET status = \"Completed\", \
                               end = NOW() \
                               WHERE id = {self.__currentMessage["id_job"]}'
            try:
                cursor.execute(updateJobQuery)
                self.__mariaClient.commit()
            except mariadb.ProgrammingError:
                print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t update jobs table' +
                    f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
                )
                self.__historyMessage = "Error in finishedJob() function: Couldn't update jobs table"
                self.__errorCount.inc()
                return True
            print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at updating jobs table' +
                f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            return False
        
        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} job isn\'t yet completed, continuing process' +
            f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return False

    # Method in charge of creating the history
    def createHistory(self):
        cursor = self.__mariaClient.cursor()
        cursor.execute(f'SELECT id FROM `groups` WHERE grp_number = {self.__currentMessage["grp_number"]} AND id_job = {self.__currentMessage["id_job"]}')
        try:
            groupId = cursor.fetchone()[0]
        except IndexError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t find group in database' +
                f'-> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__errorCount.inc()
            return True

        createQuery = f'INSERT INTO history (stage,status,created,end,message,grp_id,component) \
                        VALUES (\"jatsxml-processor\",\"In-progress\",NOW(),NULL,NULL,\
                        {groupId},\"{PODNAME}\")'
        try:
            cursor.execute(createQuery)
            self.__historyId = cursor.lastrowid
            self.__mariaClient.commit()
        except mariadb.ProgrammingError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t create a new registry in table history' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__errorCount.inc()
            return True
        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at creating new registry in history table' +
            f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return False

    # Method in charge of modifying the previously created history
    def modifyHistory(self,failed):
        cursor = self.__mariaClient.cursor()
        status = "Completed"
        if (failed):
            status = "Failed"
        updateHistoryQuery = f'UPDATE history \
                               SET status = \"{status}\", \
                               end = NOW(), \
                               message = \"{self.__historyMessage}\" \
                               WHERE id = {self.__historyId}'

        self.__historyMessage = ""

        try:
            cursor.execute(updateHistoryQuery)
            self.__historyId = cursor.lastrowid
            self.__mariaClient.commit()
            print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at modifying history' +
                f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
        except mariadb.ProgrammingError:
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} couldn\'t modify history table' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__errorCount.inc()
            return True

    # method in charge of getting the group specify in the queue message
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
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__historyMessage = "Error in getGroupFromElastic() function: Group was't found in Elasticsearch"
            self.__errorCount.inc()
            return True
        
        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at getting group from elastic' +
            f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return False

    # method in charge of processing all docs in a group, including getting the jatsxml, pusblishing to elastic and deleting group
    def processDocs(self):
        for doc in self.__currentGroup["docs"]:
            if "details" in doc and "jatsxml" in doc["details"]:
                doc["details"]["jatsxml"] = self.getJatsxml(doc["details"]["jatsxml"])
                self.__processedJatsxml.inc()
            else:
                self.__notProcessedJatsxml.inc()
            self.__elasticClient.index(index=ELASTICINDEX, document=doc, refresh='wait_for')
            print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at publishing new doc' +
                f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
        self.__elasticClient.delete(index="groups", id=self.__currentGroupId)
        print(f'{bcolors.PROCESSING}Processing:{bcolors.RESET} success at deleting group' +
            f' -> {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )
        return False

    # Method that has all the processing
    def processing(self):
        if ("id_job" not in self.__currentMessage or "grp_number" not in self.__currentMessage):
            print(f'{bcolors.FAIL}Error:{bcolors.RESET} invalid message obtain from queue' +
                f' -> {bcolors.WARNING} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
            )
            self.__errorCount.inc()
            return True
        
        if(self.updateGroup()):
            return True

        if(self.createHistory()):
            return True

        if(self.getGroupFromElastic()):
            return True
        
        if(self.processDocs()):
            return True

        if(self.finishedGroup()):
            return True
        
        if(self.finishedJob()):
            return True

        return False

    # Method used as callback for the consume
    @__processingTimePerGroup.time()
    def consume(self, ch, method, properties, msg):
        self.__currentMessage = json.loads(msg)

        print(f'{bcolors.OK}Message Receive:{bcolors.RESET} Starting Process -> {bcolors.GRAY}{str(self.__currentMessage)}')

        result = self.processing()
        if(not result and self.__historyMessage == ""):
            self.__historyMessage = "successful process"
        
        self.modifyHistory(result)

        print(f'{bcolors.OK}Group finished:{bcolors.RESET} ->' +
            f' {bcolors.GRAY} grp_number: {self.__currentMessage["grp_number"]} id_job: {self.__currentMessage["id_job"]} {bcolors.RESET}'
        )

        self.__processedGroups.inc()

        ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

    def startProcess(self):
        start_http_server(int(METRICSPORT))
        self.__consumerQueue.start_consuming()

JatsxmlProcessor()