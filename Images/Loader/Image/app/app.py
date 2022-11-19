from    datetime            import      datetime
from    time                import      sleep,      time
from    prometheus_client   import      Counter,    Summary,    start_http_server

import  os
import  json
import  pika
import  mariadb
import  requests
import  json
import  math


#---------------------------------------------------------------------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------


# RabbitMQ
RABBITHOST              =   os.getenv("RABBITHOST")
RABBITPORT              =   os.getenv("RABBITPORT")
RABBITUSER              =   os.getenv("RABBITUSER")
RABBITPASS              =   os.getenv("RABBITPASS")
RABBITDEST              =   os.getenv("RABBITDEST")


# MariaDB
MARIADBNAME             =   os.getenv("MARIADBNAME")
MARIADBHOST             =   os.getenv("MARIADBHOST")
MARIADBPORT             =   os.getenv("MARIADBPORT")
MARIADBUSER             =   os.getenv("MARIADBUSER")
MARIADBPASS             =   os.getenv("MARIADBPASS")

#BioRxiv
APIBIORXIV              =   os.getenv("APIBIORXIV")

#Pod's name
PODNAME                 =   os.getenv("HOSTNAME")

SLEEPTIME               =   os.getenv("SLEEPTIME")
PORTSERVER              =   os.getenv("PORTSERVER")


#---------------------------------------------------------------------------------------------------------------------------------------------
# CLASSES
#---------------------------------------------------------------------------------------------------------------------------------------------

#This class was taken on: https://www.delftstack.com/es/howto/python/python-print-colored-text/ 
class bcolors:
    OK                  =   '\033[92m'    #GREEN
    WARNING             =   '\033[93m'    #YELLOW
    FAIL                =   '\033[91m'    #RED
    RESET               =   '\033[0m'     #RESET COLOR



class Loader:

    CONN                =   None    #MariaDB connection
    CUR                 =   None    #MariaDB cursor
    MSG                 =   None    #Message that will be publish on queue
    PUBLISHQUEUE        =   None    #Queue where the application needs to consume
    AVGTIME             =   None    #Average time process per group
    PROCESSEDGROUPS     =   None    #Total quantity of groups has been processed
    ERRORS              =   None    #Quantity of errors that has been ocur
    JOBSDONE            =   None    #Quantity of jobs that has been processed
    STMT                =   "SELECT id,created,status,end,loader,grp_size FROM jobs WHERE status = 'new' LIMIT 1"
    AVGTIME             =   Summary(
                            'loader_avg_processing_time', 
                            'Average amount of time elapsed when processing')
    
    #Constructor method
    def __init__(self):

        #Starting server where we send metrics
        start_http_server(PORTSERVER)

        #Setting up all necessary things
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
            print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e} [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
        
        #Creating queue
        self.PUBLISHQUEUE.queue_declare(queue=RABBITDEST)

    #In case that the tables hasn't been created, we create them
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
        self.CUR.execute(jobsTable)
        self.CUR.execute(groupsTable)
        self.CONN.commit()

    #Initialize metric values
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

    #Reconnect to the queue in case there is any problem
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
            print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} Couldn't connect to RabbitMQ [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
        #Creating queues
        self.PUBLISHQUEUE.queue_declare(queue=RABBITDEST)

    #Publish to the queue the new message
    def produce(self, message):
        try:
            self.PUBLISHQUEUE.basic_publish(routing_key=RABBITDEST, body=json.dumps(message), exchange='')
        except pika.exceptions.StreamLostError:
            print(f"{bcolors.FAIL} LOADER: {bcolors.RESET} connection lost, reconnecting... [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
            self.reconnectPublishQueue()
            self.produce(message)
    
    #Realize a query to the biorxiv API to get the total of documents and creates the number of groups based on the size that the job has
    def get_info(self, grp_size):
        response = requests.get(APIBIORXIV)
        data = json.loads(response.text)
        total = data["messages"][0]["total"]

        groups = total / grp_size

        return math.ceil(groups)

    #The main loop, continuously checks for new jobs and processes it
    def transaction(self):
        while True:
            try:
                sleep(1)
                #Start a transaction
                self.CUR.execute("START TRANSACTION")
                self.process_job()
                self.CUR.execute("COMMIT")
            
            #Error handling
            except mariadb.ProgrammingError as e:
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} CREATING TABLES")
                self.initTables()
                self.ERRORS.inc()

    #This function creates the number of groups that the job needs
    def create_groups(self,length, id, grps):
            offset = 0
            print(f"{bcolors.OK}Processing: {bcolors.RESET}Starting the processing of id_job {id}")
            
            for i in range(grps):
                try:
                
                    self.CUR.execute(f"INSERT INTO groups(id_job,created,end,stage,grp_number,status,`offset`)\
                                        VALUES ({str(id)},now(),null,'Loader',{str(i)},null,{str(offset)})")
                    
                    offset += length

                    self.MSG = {"id_job":id, "grp_number": i}
                    self.produce(self.MSG)
                    self.PROCESSEDGROUPS.inc()
                    
                    print(f"{bcolors.OK}Processing: {bcolors.RESET} Group {self.MSG} has been processed succesfully.")
                
                except mariadb.ProgrammingError as e:
                    print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                    self.ERRORS.inc()

    #process_job processes a job and creates its respective groups.
    @AVGTIME.time()
    def process_job(self):
        self.CUR.execute(self.STMT)
        lis = self.CUR.fetchall()

        
        if lis != []:
            #lis always will have JUST ONE job because the SQL statement is limited by one
            try:
                for i in lis:

                    length = i[5]                           #takes the group size
                    grps = self.get_info(length)            #return the number of groups we need
                    self.create_groups(length,i[0],grps)    #create the groups

                    self.CUR.execute(f"UPDATE jobs SET \
                                status = 'IN PROGRESS', \
                                loader = '{str(PODNAME)}' \
                                WHERE id = {str(i[0])}")    #Updates the job

                self.JOBSDONE.inc()                         #Icrements the counter

                return False

            except mariadb.ProgrammingError as e:
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                self.ERRORS.inc()
        
        if lis == []:
            return True
    
    #Connects to MariaDB
    def connectMariaDB(self):
        #Connect to mariadb
        try:
            self.CONN = mariadb.connect(
                user=MARIADBUSER,
                password=MARIADBPASS,
                host=MARIADBHOST,
                port=int(MARIADBPORT),
                database=MARIADBNAME)
            
            self.CUR = self.CONN.cursor()

            print(f"{bcolors.OK}OK: {bcolors.RESET}Connection succesfully")

        except mariadb.Error as e:
            print(f"{bcolors.FAIL}ERROR: {bcolors.RESET}Error connecting to MariaDB Platform: {e}")


Loader()
