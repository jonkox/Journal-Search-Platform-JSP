import mysql.connector
import time
import datetime

MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "9xyqnMJvfy"

try:
    mariaClient = mysql.connector.connect(
        host=MARIADBHOST, 
        port= MARIADBPORT,
        user=MARIADBUSER, 
        password= MARIADBPASS, 
        database= MARIADBNAME)
    # Get Cursor
    mariadbCursor = mariaClient.cursor(prepared = True)
except:
    print("Error: Couldn't connect to MariaDB") 

def updateGrpTable(grp_number):
    # Update group's stage
    update_query = """UPDATE grupos set stage = 'downloader' where id = %s"""
    #update_query = update_query + grp_number
    mariadbCursor.execute(update_query, (grp_number,))
    mariaClient.commit()

    # Update group's status
    update_query = """UPDATE grupos set status = 'in-progress' where id = %s"""
    #update_query = update_query + grp_number
    mariadbCursor.execute(update_query, (grp_number,))
    mariaClient.commit()

    # --------------- TEST ------------------------
    print("Record Updated successfully")

    print("After updating record ")
    select_query = """SELECT stage from grupos WHERE id = %s"""
    mariadbCursor.execute(select_query, (grp_number,))
    record = mariadbCursor.fetchone()
    print(record)

    select_query = """SELECT status from grupos WHERE id = %s"""
    mariadbCursor.execute(select_query, (grp_number,))
    record = mariadbCursor.fetchone()
    print(record)

def insertTable(grp_number):
    # Check if table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            component VARCHAR(45),
            status VARCHAR(45),
            created DATETIME,
            end DATETIME DEFAULT NULL,
            message TEXT DEFAULT NULL,
            stage VARCHAR(45),
            grp_id INT REFERENCES grupos(id)
        )
    """
    mariadbCursor.execute(create_table_query)
    mariaClient.commit()
    
    stage = 'downloader'
    status = 'in-progress'
    
    # LLave foranea para referenciar al grupo
    grp_id_query = """SELECT id from grupos WHERE id = %s"""
    mariadbCursor.execute(grp_id_query, (grp_number,))
    grp_id = mariadbCursor.fetchone()[0]

    component = 'downloader' # Identificador del pod, TEMPORALMENTE downloader

    current_datetime = datetime.datetime.now()
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    insert_query = """INSERT INTO history (component,status,created,grp_id,stage) VALUES (%s,%s,%s,%s,%s)"""
    values = (component, status ,current_datetime_str, grp_id, stage)
    mariadbCursor.execute(insert_query,values)
    mariaClient.commit()
   

#updateGrpTable('1')
insertTable('0')