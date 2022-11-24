import mariadb
import datetime

MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "mzx1nljUaW"

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
    mariadbCursor = mariaClient.cursor(prepared = True)
    mariadbCursor.execute("SET GLOBAL time_zone = '-6:00'")
    mariaClient.commit()

    current_datetime = datetime.datetime.now()
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    insert_query = """INSERT INTO fechas (fecha) VALUES (%s)"""
    mariadbCursor = mariaClient.cursor(prepared = True)
    mariadbCursor.execute(insert_query,(current_datetime_str,))
    mariaClient.commit()

except:
    print("Error: Couldn't connect to MariaDB") 