import json
import pika
import elastic_transport
import mariadb
import datetime
import json
import os

from elasticsearch import Elasticsearch
from prometheus_client import Gauge, start_http_server
from time import time
from urllib.request import urlopen

# ------------- Used for testing without environment variables -----------
# ELASTICHOST = "http://localhost"
# ELASTICPORT = "32500"
# ELASTICUSER = "elastic" 
# ELASTICPASS = "Ogi0LyLHE9SgXwzp" 
# ELASTICINDEX = "groups"

# RABBITHOST = 'localhost'
# RABBITPORT = '30100'
# RABBITUSER = 'user'
# RABBITPASS = 'C12zaCZPRM1FCGpD'
# RABBITQUEUENAMEINPUT = 'loader'
# RABBITQUEUENAMEOUTPUT ='downloader'

# MARIADBNAME = "my_database"
# MARIADBHOST = "localhost"
# MARIADBPORT = 32100
# MARIADBUSER = "root"
# MARIADBPASS = "mzx1nljUaW"

# COMPONENT = 'downloader'

# URL = "https://api.biorxiv.org/covid19/"

# ------------ ENVIRONMENT  VARIABLES FOR CONNECTIONS -------

# Elasticsearch
ELASTICHOST = os.getenv("ELASTICHOST")
ELASTICPORT = os.getenv("ELASTICPORT")
ELASTICUSER = os.getenv("ELASTICUSER")
ELASTICPASS = os.getenv("ELASTICPASS")
ELASTICINDEX = "groups"

# RabbitMQ
RABBITHOST = os.getenv("RABBITHOST")
RABBITPORT = os.getenv("RABBITPORT")
RABBITUSER = os.getenv("RABBITUSER")
RABBITPASS = os.getenv("RABBITPASS")
RABBITQUEUENAMEINPUT = os.getenv("RABBITQUEUENAMEINPUT")
RABBITQUEUENAMEOUTPUT = os.getenv("RABBITQUEUENAMEOUTPUT")

# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

COMPONENT = os.getenv("HOSTNAME")

URL = os.getenv("APIBIORVIXURL")
URL += "covid19/"

METRICSPORT = os.getenv("METRICSPORT")

# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR

class Downloader:
    # Variables for metrics
    time = 0
    processedGroups_metrics = 0
    downloadedDocs = 0
    amountOfErrors = 0
    totalProcessingTime = None
    avgProcessingTime = None
    startingTime = None
    
    processedGroups_offset = 0

    ESConnection = None
    MariaClient = None
    mariadbCursor = None

    grp_number = None
    id_job = None
    grp_id = None

    #Constructor method
    def __init__(self):
        # Initialize variables for metrics
        self.totalProcessingTime = Gauge(
            'downloader_total_processing_time', 
            'Total amount of time elapsed when processing')
        
        self.avgProcessingTime = Gauge(
            'downloader_avg_processing_time', 
            'Average amount of time elapsed when processing')

        self.numberOfProcessedGroups = Gauge(
            'downloader_number_processed_groups', 
            'Number of groups process by downloader')
        
        self.amountDownloadedDocuments = Gauge(
            'downloader_amount_downloaded_docs', 
            'Number of documents downloaded by downloader')

        self.totalProcessingTime.set(0)
        self.avgProcessingTime.set(0)
        self.numberOfProcessedGroups.set(0)
        self.amountDownloadedDocuments.set(0)

        # #Starting server where we send metrics
        start_http_server(int(METRICSPORT))

        self.connectElastic(ELASTICHOST,ELASTICPORT,ELASTICUSER,ELASTICPASS)
        self.connectDbMaria(MARIADBHOST,MARIADBPORT,MARIADBUSER,MARIADBPASS,MARIADBNAME) 
        self.connectRabbitmq(RABBITUSER, RABBITPASS, RABBITHOST, RABBITPORT, RABBITQUEUENAMEINPUT)

    #----------------------------------------------------------------------- 
    # Function that creates a rabbitMQ connection
    #----------------------------------------------------------------------- 
    def connectRabbitmq(self, user, password, host, port, queueName):
        # Connect to rabbtimq
        rabbitUserPass = pika.PlainCredentials(user, password)

        rabbitConnectionParameters = pika.ConnectionParameters(
            host= host, 
            port= port,
            credentials= rabbitUserPass
        )

        try:
            rabbitConnection = pika.BlockingConnection(rabbitConnectionParameters)
            channel = rabbitConnection.channel()
            channel.queue_declare(queue = queueName)
            channel.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            raise Exception("Error: Couldn't connect to RabbitMQ")

        channel.basic_consume(queue= queueName, auto_ack=False, on_message_callback=self.callback)
        channel.start_consuming()

    #----------------------------------------------------------------------- 
    # Function that creates an elastic client
    #----------------------------------------------------------------------- 
    def connectElastic(self,pHost,pPort,pUser,pPass):
        try:
            self.ElasticClient = Elasticsearch(
                    pHost+":"+pPort,
                    basic_auth=(pUser,pPass)
                )

        except elastic_transport.ConnectionError:
            raise Exception ("Error: Couldn't connect to ElasticSearch")

    #-----------------------------------------------------------------------         
    # Function that creates a maria client
    #----------------------------------------------------------------------- 
    def connectDbMaria(self,pHost,pPort,pUser,pPass,pName):
        try:
            self.MariaClient = mariadb.connect(
                    host=pHost, 
                    port= int(pPort),
                    user=pUser, 
                    password= pPass, 
                    database= pName)
            # Get Cursor and set to Costa Rica's timezone
            self.mariadbCursor = self.MariaClient.cursor(prepared = True)
            self.mariadbCursor.execute("SET time_zone = '-6:00'")
            self.MariaClient.commit()

        except:
            print("Error: Couldn't connect to MariaDB") 
    
    #-----------------------------------------------------------------------         
    # Function that updates stage
    #----------------------------------------------------------------------- 
    def updateGrpTable(self):
        # Update group's stage and status
       
        update_query = """UPDATE groups set 
                            stage = 'downloader', 
                            status = 'in-progress',
                            id = last_insert_id(id)
                            where grp_number = %s AND 
                            id_job = %s"""
        
        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(update_query, (self.grp_number,self.id_job))
        self.grp_id = self.mariadbCursor.lastrowid
        self.MariaClient.commit()
    
    #-----------------------------------------------------------------------         
    # Function that inserts record into history table
    #----------------------------------------------------------------------- 
    def insertHistoryTable(self):
        # Check if table doesn't exist
        create_table_query = """
            CREATE TABLE IF NOT EXISTS history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                component VARCHAR(45),
                status VARCHAR(45),
                created DATETIME,
                end DATETIME DEFAULT NULL,
                message TEXT DEFAULT NULL,
                stage VARCHAR(45),
                grp_id INT REFERENCES groups(id)
            )
        """

        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(create_table_query)
        self.MariaClient.commit()

        stage = 'downloader'
        status = 'in-progress'

        # Get created datetime 
        current_datetime = datetime.datetime.now()
        current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        # Insert data into History table
        insert_query = """INSERT INTO history (component,status,created,grp_id,stage) VALUES (%s,%s,%s,%s,%s)"""
        values = (COMPONENT, status ,current_datetime_str, self.grp_id, stage)
        
        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(insert_query,values)
        self.MariaClient.commit()
    
    #-----------------------------------------------------------------------         
    # Function that returns 30 documents from given start
    #----------------------------------------------------------------------- 
    def get30Docs(self, start):
        new_url = URL + str(start)
       
        # Get response from bioRxiv API
        urlResult = urlopen(new_url)

        # Get JSON with API response
        data_json = json.loads(urlResult.read())

        # Get all documents from API
        collection = data_json["collection"]

        return collection
    
    #-----------------------------------------------------------------------         
    # Function that downloads and publishes to ES the documents from group
    #----------------------------------------------------------------------- 
    def publishDocs(self):
        # Get group size 
        grp_size_query = """SELECT grp_size from jobs WHERE id = %s"""
        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(grp_size_query, (self.id_job,))
        grp_size = int(self.mariadbCursor.fetchone()[0])

        docs = []
        self.processedGroups_offset = int(self.grp_number)

        if grp_size <= 30:
            start = self.processedGroups_offset * grp_size
            collection = self.get30Docs(start)
            
            for i in range (0, grp_size):
                docs.append(collection[i])
        else:
            iter = 0
            batches = grp_size // 30
            extraBatch = int(((grp_size/30) % 1) * 30)

            # Get docs from complete groups of 30
            while iter < batches:
                start = (self.processedGroups_offset * grp_size) + (30 * iter)
                collection = self.get30Docs(start)

                for i in range (0, 30):
                    docs.append(collection[i])

                iter += 1
                
            # Get docs from remaining amount smaller than 30
            start = (self.processedGroups_offset * grp_size) + (30 * iter)
            collection = self.get30Docs(start) 

            for i in range (0, extraBatch):
                docs.append(collection[i])

        doc = {
            "id_job": str(self.id_job),
            "grp_number": str(self.grp_number),
            "docs": docs
        }

        message_json = json.dumps(doc)
     
        self.ElasticClient.options(request_timeout=60).index(index=ELASTICINDEX,
                                                            document=message_json,
                                                            refresh='wait_for')
        
        self.downloadedDocs += grp_size

    #-----------------------------------------------------------------------         
    # Function that updates record from history
    #----------------------------------------------------------------------- 
    def updateHistoryTable(self, status, message):
        """
        Following data to update:
        status: completed/error
        end: tiempo actual
        message: si se dio un error se guarda aquí
        """
        history_id_query = """SELECT id from history WHERE grp_id = %s"""
        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(history_id_query, (self.grp_id,))
        history_id = int(self.mariadbCursor.fetchone()[0])
        
        update_history_query1 = """UPDATE history SET status = %s WHERE id = %s"""
        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(update_history_query1, (status,history_id,))

        # Get end datetime 
        current_datetime = datetime.datetime.now()
        current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        update_history_query2 = """UPDATE history SET end = %s WHERE id = %s"""
        self.mariadbCursor = self.MariaClient.cursor(prepared = True)
        self.mariadbCursor.execute(update_history_query2, (current_datetime_str,history_id,))
        self.MariaClient.commit()

        if status == 'error':
            update_history_query3 = """UPDATE history SET message = %s WHERE id = %s"""
            self.mariadbCursor = self.MariaClient.cursor(prepared = True)
            self.mariadbCursor.execute(update_history_query3, (message,history_id,))
            self.MariaClient.commit()

    #-----------------------------------------------------------------------         
    # Function that calls downloader tasks
    #----------------------------------------------------------------------- 
    def workForPod(self, jsonObject):
        # Start timer for metrics
        self.startingTime = time()

        # Get job_id from the document that was received
        self.id_job = jsonObject["id_job"]

        # Get group_id from the document that was received
        self.grp_number = jsonObject["grp_number"]

        # -------- Update group table ---------------
        self.updateGrpTable()
        print(f"{bcolors.OK} Downloader: {bcolors.RESET} Group table updated")

        # -------- Add record to History table ------
        self.insertHistoryTable()
        print(f"{bcolors.OK} Downloader: {bcolors.RESET} Added record to history table")

        # -------- Download and publish documents ---------------
        self.publishDocs()
    
        print(f"{bcolors.OK} Downloader: {bcolors.RESET} Published documents")

    #-----------------------------------------------------------------------         
    # Function that sends message to output queue
    #----------------------------------------------------------------------- 
    def sendMessage(self, user, password, host, port, queueName):
        # Connect to rabbtimq
        rabbitUserPass = pika.PlainCredentials(user, password)

        rabbitConnectionParameters = pika.ConnectionParameters(
            host= host, 
            port= port,
            credentials= rabbitUserPass
        )

        try:
            rabbitConnection = pika.BlockingConnection(rabbitConnectionParameters)
            channel = rabbitConnection.channel()
            channel.queue_declare(queue = queueName)
            channel.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            raise Exception("Error: Couldn't connect to RabbitMQ")

        message = {
            "id_job": str(self.id_job),
            "grp_number": str(self.grp_number)
        }

        message_json = json.dumps(message)
        channel.basic_publish(exchange='', routing_key=queueName, body=message_json)

    #-----------------------------------------------------------------------         
    # Function that sets metrics for Prometheus
    #----------------------------------------------------------------------- 
    def metrics(self):
        self.time += (time() - self.startingTime)
        self.processedGroups_metrics += 1
        self.numberOfProcessedGroups.set(self.processedGroups_metrics)
        self.totalProcessingTime.set(self.time)
        self.avgProcessingTime.set(self.time/self.processedGroups_metrics)
        self.amountDownloadedDocuments.set(self.downloadedDocs)
    
    #-----------------------------------------------------------------------         
    # Consume from rabbitMQ queue
    #----------------------------------------------------------------------- 
    def callback(self, ch, method, properties, body):
        print(f"{bcolors.OK} Downloader: {bcolors.RESET} Message was received")
        json_object = json.loads(body)
        
        try:
            self.workForPod(json_object)
            
            # If work was successful then update history table
            self.updateHistoryTable('completed', "")

            # Update group status
            update_group_query = """UPDATE groups SET status = %s WHERE id = %s"""
            self.mariadbCursor = self.MariaClient.cursor(prepared = True)
            self.mariadbCursor.execute(update_group_query, ('completed',self.grp_id,))
            self.MariaClient.commit()

            # Send message to output queue for next component
            self.sendMessage(RABBITUSER, RABBITPASS, RABBITHOST, RABBITPORT, RABBITQUEUENAMEOUTPUT)

            # Feed metrics
            self.metrics()

            print(f"{bcolors.OK} Downloader: {bcolors.RESET} Process finished")

            # This notifies that the message was received succesfully
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
        
        except Exception as error:
            # If work was unsuccessful then update history table with error message
            self.updateHistoryTable('error', str(error))

            # Update group status
            update_group_query = """UPDATE groups SET status = %s WHERE grp_number = %s AND id_job = %s"""
            self.mariadbCursor = self.MariaClient.cursor(prepared = True)
            self.mariadbCursor.execute(update_group_query, ('completed',self.grp_number,self.id_job))
            self.MariaClient.commit()

            print(f"{bcolors.FAIL} Downloader: {bcolors.RESET} Failed to download group")
        
            # Send message to output queue for next component
            self.sendMessage(RABBITUSER, RABBITPASS, RABBITHOST, RABBITPORT, RABBITQUEUENAMEOUTPUT)

            # Feed metrics
            self.metrics()

            # This notifies that the message was received succesfully
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

Downloader()