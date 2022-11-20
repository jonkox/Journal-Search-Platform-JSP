import pika
import os

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

    # Open file for testing
    localFile = os.path.join(os.path.dirname(__file__), 'inputmsg.json')
    f = open(localFile,  "r")
    dataFromFile = f.read()

    # Simulation: Send message from "loader" to downloader app
    channel.queue_declare(queue = QUEUE_NAME_INPUT)
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME_INPUT, body=dataFromFile)


    print(f"{bcolors.OK} Simulation: Got msg from queue, start process {bcolors.RESET}")
    print(dataFromFile)

    connection.close()

loaderFinishedProcess()