
import pymysql

def get_pyconfig(database):
    pyconfig = {
        #'host':'192.168.100.109',
        'host':'label_db',
        'port':3306,
        'user':'root',
        'password':'yd_db_pass',
        'database': database
    }
    return pyconfig 


def get_db(database):
    pyconfig = get_pyconfig(database)
    db = pymysql.connect(**pyconfig)
    return db

def sqlquery(database, sql):
    db = get_db(database)
    cursor = db.cursor(pymysql.cursors.DictCursor)
    cursor.execute(sql)
    result = cursor.fetchall()
    db.commit()
    cursor.close()
    return result

def db_sport(sql):
    return sqlquery('sport', sql)

def db_file(sql):
    return sqlquery('file', sql)