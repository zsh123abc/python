
import pymysql
import threading
from DBUtils.PooledDB import PooledDB



def sqlquery(sql):
    pyconfig = {
    #'host':'192.168.100.109',
    'host':'label_db',
    'port':3306,
    'user':'root',
    'password':'yd_db_pass',
    'database': 'file'
    }

    
    db = pymysql.connect(**pyconfig)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    while True:
        try:
            db.ping()
            break
        except:
            db.ping(True)
    #db.ping(reconnect=True) 
     
    
    cursor.execute(sql)
   
    result = cursor.fetchall()
    
    db.commit()
    
    #cursor.close()
    return result

def db_file(sql):
    #lock = threading.Lock() 
    #lock.acquire()
    res = sqlquery(sql)
    #lock.release()
    return res