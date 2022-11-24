
import mariadb
import random



# MariaDB
MARIADBNAME = "my_database"
MARIADBHOST = "localhost"
MARIADBPORT = 32100
MARIADBUSER = "root"
MARIADBPASS = "jtGlurMZin"

def connectMariaDB():
    val = True

    
    #Connect to mariadb
    try:
        conn = mariadb.connect(
            user=MARIADBUSER,
            password=MARIADBPASS,
            host=MARIADBHOST,
            port=MARIADBPORT,
            database=MARIADBNAME)
        cur = conn.cursor()
        print("Connection succesfully")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")

    if val:
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
        
        cur.execute("delete from history where true = true")
        cur.execute("delete from `groups` where true = true")
        cur.execute("delete from jobs where true = true")

        #cur.execute("DROP TABLE IF EXISTS my_database.groups")
        #cur.execute("DROP TABLE IF EXISTS my_database.jobs")
        cur.execute(jobsTable)
        cur.execute(groupsTable)
        conn.commit()

        # {str(random.randint(10,2000))}
        for i in range(1):
            print("INSERTANDO JOBS")
            cur.execute(f"insert INTO my_database.jobs(created,status,end,loader,grp_size) values(now(),'NEW',null,null,50)")
        conn.commit()
    
    if not val:
        cur.execute("select * from jobs")
        s = cur.fetchall()
        print(s)


connectMariaDB()