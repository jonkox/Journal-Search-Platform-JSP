import mariadb

MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "9xyqnMJvfy"

"""
# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")
"""

try:
    mariaClient = mariadb.connect(
        host=MARIADBHOST, 
        port= MARIADBPORT,
        user=MARIADBUSER, 
        password= MARIADBPASS, 
        database= MARIADBNAME)
    # Get Cursor
    mariadbCursor = mariaClient.cursor()
except:
    print("Error: Couldn't connect to MariaDB") 