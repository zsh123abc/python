import pymysql
import threading
from DBUtils.PooledDB import PooledDB

class pools():
    def __init__(self):
        self.pool = self.mysql_connection()

    def get_connect(self):
        if self.pool:
            conn = self.pool.connection()
            
        return conn
    # print(th, '链接被拿走了', conn1._con)
    # print(th, '池子里目前有', pool._idle_cache, '\r\n')
    def sqlquery(self,sql):
        conn = self.get_connect()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return result

    def mysql_connection(self):
        maxconnections = 50
        pool = PooledDB(
            pymysql,
            maxconnections,
            host='label_db',
            user='root',
            port=3306,
            passwd='yd_db_pass',
            db='file',
            use_unicode=True)
        return pool

    def sqlquery1(sql):
        pool = mysql_connection()
        con = pool.connection()
        cur = con.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql)
        result = cur.fetchall()
        con.commit()
        cur.close()
        con.close()
        return result

def db_file(sql):
    pool = pools()
    return pool.sqlquery(sql)