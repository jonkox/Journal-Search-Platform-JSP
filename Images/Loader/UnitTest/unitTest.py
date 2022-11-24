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
import  unittest
import  random


#---------------------------------------------------------------------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------


#BioRxiv
APIBIORXIV              =   "https://api.biorxiv.org/covid19/0"

#Pod's name
PODNAME                 =   "Loader-Unit-Test"

#Control Variables
SLEEPTIME               =   1
PORTSERVER              =   6343 
JOBSNUM                 =   5

#MariaDB
MARIADBNAME             =   "my_database"
MARIADBHOST             =   "localhost"
MARIADBPORT             =   32100
MARIADBUSER             =   "root"
MARIADBPASS             =   "3VopN5R26q"

#RABBITMQ
RABBITHOST              =   "localhost"         
RABBITPORT              =   "30100"             
RABBITUSER              =   "user"              
RABBITPASS              =   "kU0eN0mRWq4Q0eVu"  
RABBITDEST              =   "REGEX-FUENTE"      


#---------------------------------------------------------------------------------------------------------------------------------------------
# CLASSES
#---------------------------------------------------------------------------------------------------------------------------------------------

#This class was taken on: https://www.delftstack.com/es/howto/python/python-print-colored-text/ 
class bcolors:
    OK                  =   '\033[92m'      #GREEN
    WARNING             =   '\033[93m'      #YELLOW
    FAIL                =   '\033[91m'      #RED
    RESET               =   '\033[0m'       #RESET COLOR



class Loader(unittest.TestCase):

    CONN                =   None            #MariaDB connection
    CUR                 =   None            #MariaDB cursor
    MSG                 =   None            #Message that will be publish on queue
    PUBLISHQUEUE        =   None            #Queue where the application needs to consume
    AVGTIME             =   None            #Average time process per group
    PROCESSEDGROUPS     =   None            #Total quantity of groups has been processed
    ERRORS              =   None            #Quantity of errors that has been ocur
    JOBSDONE            =   None            #Quantity of jobs that has been processed
    STMT                =   "SELECT id,created,status,end,loader,grp_size FROM LoaderUnitTest.jobs WHERE status = 'new' LIMIT 1"
    AVGTIME             =   Summary(
                            'loader_avg_processing_time', 
                            'Average amount of time elapsed when processing')
    TOTALMESSAGES       =   0
    
    #Constructor method
    def __init__(self):

        #Starting server where we send metrics
        start_http_server(int(PORTSERVER))

        #Setting up all necessary things
        self.connectMariaDB()
        self.initTables()
        #self.initQueue()
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
        self.CUR.execute("DROP DATABASE IF EXISTS LoaderUnitTest")
        self.CUR.execute("CREATE DATABASE IF NOT EXISTS LoaderUnitTest")

        jobsTable = "CREATE TABLE IF NOT EXISTS LoaderUnitTest.jobs ( \
                            id INT NOT NULL AUTO_INCREMENT, \
                            created DATETIME, \
                            status VARCHAR(45), \
                            end DATETIME, \
                            loader VARCHAR(45), \
                            grp_size INT, \
                            PRIMARY KEY (id) \
                        )"

        groupsTable = "CREATE TABLE IF NOT EXISTS LoaderUnitTest.groups ( \
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
        self.CUR.execute("DROP TABLE IF EXISTS LoaderUnitTest.groups")
        self.CUR.execute("DROP TABLE IF EXISTS LoaderUnitTest.jobs")
        self.CUR.execute(jobsTable)
        self.CUR.execute(groupsTable)
        self.CONN.commit()

        for i in range(JOBSNUM):
            self.CUR.execute(f"insert INTO LoaderUnitTest.jobs(created,status,end,loader,grp_size) values(now(),'NEW',null,null,{str(random.randint(10,2000))})")
        
        self.CONN.commit()
        
        self.CUR.execute("USE LoaderUnitTest")

    #Initialize metrics values
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
        self.TOTALMESSAGES = data["messages"][0]["total"]
        groups = total / grp_size

        return math.ceil(groups)

    #The main loop, continuously checks for new jobs and processes it
    def transaction(self):
        self.CUR.execute("select count(*) from jobs")
        jobs = self.CUR.fetchall()[0][0]

        for i in range(jobs): #In this unit test this is the main difference, now it is a for cycle instead of a while true
            try:
                sleep(int(SLEEPTIME))
                
                #Start processing the job.
                self.process_job()

            #Error handling
            except mariadb.ProgrammingError as e:
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                self.ERRORS.inc()

    #This function creates the number of groups that the job needs
    def create_groups(self,length, id, grps):
            offset = 0
            print(f"{bcolors.OK}Processing: {bcolors.RESET}Starting the processing of id_job {id}")
            
            for i in range(grps):
                try:

                    self.CUR.execute(f"INSERT INTO LoaderUnitTest.groups(id_job,created,end,stage,grp_number,status,`offset`) \
                                        VALUES ({str(id)},now(),null,'Loader',{str(i)},null,{str(offset)})")
                    self.CONN.commit()
                    offset += length

                    self.MSG = {"id_job":id, "grp_number": i}
                    #self.produce(self.MSG)          here it suppose to send a message to the queue
                    self.PROCESSEDGROUPS.inc()
                    
                    print(f"{bcolors.OK}Processing: {bcolors.RESET} Group {self.MSG} has been processed succesfully.")
                
                except mariadb.ProgrammingError as e:
                    print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                    self.ERRORS.inc()

    #process_job processes a job and creates its respective groups.
    @AVGTIME.time()
    def process_job(self):
        #This statement takes 1 job to be processed and at the same time updates it.
        stmt = f"UPDATE LoaderUnitTest.jobs SET `status` = 'In-progress', loader='{str(PODNAME)}' ,id=last_insert_id(id) WHERE `status` = 'new' LIMIT 1"
        self.CUR.execute(stmt)
        self.CONN.commit()
        id_job = self.CUR.lastrowid
        if id_job != None:
            #lis always will have JUST ONE job because the SQL statement is limited by one
            try:
                self.CUR.execute(f"SELECT grp_size FROM jobs WHERE id = {id_job}")      #Updates the job
                length = self.CUR.fetchone()[0]                                         #takes the group size
                grps = self.get_info(length)                                            #return the number of groups we need
                self.create_groups(length,id_job,grps)                                  #create the groups

                self.JOBSDONE.inc()                                                     #Icrements the counter
                return False

            except mariadb.ProgrammingError as e:
                print(f"{bcolors.FAIL}ERROR: {bcolors.RESET} {e}")
                self.ERRORS.inc()
        else:
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