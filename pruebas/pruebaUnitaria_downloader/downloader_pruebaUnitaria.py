import pika
import os
from time import sleep

# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR

def loaderFinishedProcess():
    rabbitUserPass = pika.PlainCredentials("user","C12zaCZPRM1FCGpD")
    rabbitConnectionParameters = pika.ConnectionParameters(
            host='localhost', 
            port='30100',
            credentials=rabbitUserPass
        )
    connection = pika.BlockingConnection(rabbitConnectionParameters)
    channel = connection.channel()

    QUEUE_NAME_INPUT = 'loader' 

    file0 = "inputmsg0.json"
    file1 = "inputmsg1.json"
    file2 = "inputmsg2.json"
    file3 = "inputmsg3.json"

    files = []
    files.append(file0)
    files.append(file1)
    files.append(file2)
    files.append(file3)

    # Open file for testing
    for file in files:
        sleep(2)
        localFile = os.path.join(os.path.dirname(__file__), file)
        f = open(localFile,  "r")
        dataFromFile = f.read()

        # Simulation: Send message from "loader" to downloader app
        channel.queue_declare(queue = QUEUE_NAME_INPUT)
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME_INPUT, body=dataFromFile)

        print(f"{bcolors.OK} Simulation: Got msg from queue, start process {bcolors.RESET}")
        print(dataFromFile)


loaderFinishedProcess()