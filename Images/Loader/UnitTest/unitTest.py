from    time                import      sleep,time
from    prometheus_client   import      Counter, Gauge ,Summary,start_http_server
from    datetime            import      datetime

import os
import json
import pika

import mariadb
import requests
import json
import math


#---------------------------------------------------------------------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------


# Elasticsearch
ELASTICHOST         =   os.getenv("ELASTICHOST")
ELASTICPORT         =   os.getenv("ELASTICPORT")
ELASTICUSER         =   os.getenv("ELASTICUSER")
ELASTICPASS         =   os.getenv("ELASTICPASS")

# MariaDB
MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "3VopN5R26q"

"""
# RabbitMQ
RABBITHOST          =   os.getenv("RABBITHOST")
RABBITPORT          =   os.getenv("RABBITPORT")
RABBITUSER          =   os.getenv("RABBITUSER")
RABBITPASS          =   os.getenv("RABBITPASS")
SOURCEQUEUE         =   os.getenv("SOURCEQUEUE")
DESTQUEUE           =   os.getenv("DESTQUEUE")
"""
#BioRx
APIBIORXIV = "https://api.biorxiv.org/covid19/0" #os.getenv("APIBIORXIV")

PODID = "jajajaj"


#---------------------------------------------------------------------------------------------------------------------------------------------
# GLOBAL VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------

"""
#ELASTICSEACH
ELASTICHOST         =   "http://localhost"  #os.getenv("ELASTICHOST")
ELASTICPORT         =   "32500"             #os.getenv("ELASTICPORT")
ELASTICPASS         =   "RYcgQ5MSpmjeRcjj"  #os.getenv("ELASTICPASS")
ELASTICUSER         =   "elastic"
"""

#RABBITMQ
RABBITHOST          =   "localhost"         #os.getenv("RABBITHOST")
RABBITPORT          =   "30100"             #os.getenv("RABBITPORT")
RABBITUSER          =   "user"              #os.getenv("RABBITUSER")
RABBITPASS          =   "kU0eN0mRWq4Q0eVu"  #os.getenv("RABBITPASS")
RABBITQUEUENAME     =   "REGEX-FUENTE"      #os.getenv("RABBITQUEUENAME")
SOURCEQUEUE         =   "regex_queue"       #Name of the queue that the application need to consume
DESTQUEUE           =   "ready"             #Name of the queue that the application need to produce


"""
#RABBITMQ
RABBITHOST          =   "localhost"         #os.getenv("RABBITHOST")
RABBITPORT          =   "30100"             #os.getenv("RABBITPORT")
RABBITUSER          =   "user"              #os.getenv("RABBITUSER")
RABBITPASS          =   "kU0eN0mRWq4Q0eVu"  #os.getenv("RABBITPASS")
RABBITQUEUENAME     =   "REGEX-FUENTE"      #os.getenv("RABBITQUEUENAME")
SOURCEQUEUE         =   "regex_queue"       #Name of the queue that the application need to consume
DESTQUEUE           =   "ready"             #Name of the queue that the application need to produce


# MariaDB
MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "3VopN5R26q"
"""

#---------------------------------------------------------------------------------------------------------------------------------------------
# CLASSES
#---------------------------------------------------------------------------------------------------------------------------------------------

#This class was taken on: https://www.delftstack.com/es/howto/python/python-print-colored-text/ 
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR



class Loader:

    conn = None
    cur = None
    stmt = "select id,created,status,end,loader,grp_size from jobs where status = 'new' limit 1"
    msg = {}

    docs                =   []      #List of documents thas has been transform
    REGEX               =   None    #Regular expression taken from the job document
    FIELD               =   None    #Field where the REGEX has to be applied
    NEWFIELD            =   None    #New field that need to be created into the document
    INITIALRESPONSE     =   None    #Gets the jobs from the index jobs
    JOB                 =   None    #Just one job at the time, has all the config file
    PUBLISHQUEUE        =   None    #Queue where the application needs to consume
    CONSUMERQUEUE       =   None    #Destination queue, ehre the applications need to produce
    SIZE                =   None    #Size of the partition based on the job document
    DOCID               =   None    #Job id, not the fiel "job_id", it's own ID
    ACTUALMESSAGE       =   None    #Most recent message taken from the queue
    ELASTICCLIENT       =   None    #Connection to ElasticSearch
    TIME                =   0       #Time that a group has been processed
    PROCESSGROUPS       =   0       #Quantity of groups that has been processed
    TOTALTIME           =   None    #Total time the app has processed
    AVGTIME             =   None    #Average time process per group
    PROCESSEDGROUPS     =   None    #Total quantity of groups has been processed
    ERRORS = None
    JOBSDONE = None
    AVGTIME = Summary(
            'loader_avg_processing_time', 
            'Average amount of time elapsed when processing'
        )

    #Constructor method
    def __init__(self):

        #Initialize metrics variables
        


        #Starting server where we send metrics
        start_http_server(6943)

        self.connectMariaDB()
        self.initTables()
        self.initQueue()
        self.initMetrics()
        
        self.transaction()

    #Initialize queues, it creates source and destination queue to the processor
    def initQueue(self):
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
            self.PUBLISHQUEUE = pika.BlockingConnection(rabbitParameters).channel()

        except pika.exceptions.AMQPConnectionError as e:
            # We can't continue without a queue to publish our results
            print(f"{bcolors.FAIL} LOADER: {bcolors.RESET} {e} [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
        
        #Creating queues

        self.PUBLISHQUEUE.queue_declare(queue=DESTQUEUE)

    def initTables(self):
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
        self.cur.execute(jobsTable)
        self.cur.execute(groupsTable)
        self.conn.commit()

    def initMetrics(self):
        self.PROCESSEDGROUPS = Counter(
            'loader_number_processed_groups', 
            'Number of groups processed by LOADER'
        )

        self.ERRORS = Counter(
            'loader_number_errors', 
            'Number of errors processed by LOADER'
        )

        self.JOBSDONE = Counter(
            'loader_number_processed_jobs', 
            'Number of Jobs processed by LOADER'
        )



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
            self.PUBLISHQUEUE = pika.BlockingConnection(rabbitParameters).channel()
        except pika.exceptions.AMQPConnectionError as e:
            # We can't continue without a queue to publish our results
            print(f"{bcolors.FAIL} LOADER: {bcolors.RESET} Couldn't connect to RabbitMQ [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
        #Creating queues
        self.PUBLISHQUEUE.queue_declare(queue=DESTQUEUE)

    #Publish to the queue the new message
    def produce(self, message):
        try:
            self.PUBLISHQUEUE.basic_publish(routing_key=DESTQUEUE, body=json.dumps(message), exchange='')
        except pika.exceptions.StreamLostError:
            print(f"{bcolors.FAIL} LOADER: {bcolors.RESET} connection lost, reconnecting... [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
            self.reconnectPublishQueue()
            self.produce(message)
    
    #Method that constantly checks queue waiting for new messages
    def startProcess(self):
        self.initQueues()
        start_http_server(6943)

        self.transaction()
        self.CONSUMERQUEUE.start_consuming()
    
    def get_info(self, grp_size):
        response = requests.get(APIBIORXIV)
        data = json.loads(response.text)
        total = data["messages"][0]["total"]

        grupos = total / grp_size

        return math.ceil(grupos)


    def transaction(self):
        while True:
            try:
                sleep(1)
                self.cur.execute("START TRANSACTION")
                self.process_job()
                self.cur.execute("COMMIT")
            except mariadb.ProgrammingError as e:
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} CREATING TABLES")
                self.initTables()


    def create_groups(self,length, id, grps):
            offset = 0
            print(f"Procesando JOB con ID {id}")
            for i in range(grps):
                self.cur.execute(f"INSERT INTO groups(id_job,created,end,stage,grp_number,status,`offset`) VALUES ({str(id)},now(),null,'Loader',{str(i)},null,{str(offset)})")
                offset += length
                self.msg = {"id_job":id,
                            "grp_number": i}
                self.produce(self.msg)
                self.PROCESSEDGROUPS.inc()
                print(f"Grupo {i} del job {id} insertado")

    @AVGTIME.time()
    def process_job(self):
        self.cur.execute(self.stmt)
        lis = self.cur.fetchall()

        if lis != []:
            for i in lis:
                length = i[5]
                grps = self.get_info(length)
                self.create_groups(length,i[0],grps) 
            self.cur.execute(f"UPDATE jobs SET \
                            status = 'IN PROGRESS', \
                            loader = '{str(PODID)}' \
                            WHERE id = {str(i[0])}")
            self.JOBSDONE.inc()
            return False
            
        if lis == []:
            return True
    def connectMariaDB(self):
        #Connect to mariadb
        try:
            self.conn = mariadb.connect(
                user=MARIADBUSER,
                password=MARIADBPASS,
                host=MARIADBHOST,
                port=MARIADBPORT,
                database=MARIADBNAME)
            self.cur = self.conn.cursor()
            print("Connection succesfully")
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")


Loader()
