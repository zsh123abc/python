
import pymysql

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

def sqlquery(sql):
    cursor.execute(sql)
    result = cursor.fetchall()
    db.commit()
    #cursor.close()
    return result

def db_file(sql):
    return sqlquery(sql)