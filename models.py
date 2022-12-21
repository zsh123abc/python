import pymysql
import threading
from DBUtils.PooledDB import PooledDB



def sqlquery(sql):
    pyconfig = {
    #'host':'192.168.100.98',
    'host':'label_db',
    'port':3306,
    'user':'root',
    'password':'yd_db_pass',
    'database': 'file'
    }

    # pymysql.connect() 远程连接数据库，**代表收集关键字参数。
    db = pymysql.connect(**pyconfig)
    # cursor 游标：一次只拿一条数据，pymysql.cursors.DictCursor表示读取的数据为字典类型
    cursor = db.cursor(pymysql.cursors.DictCursor)
    while True:
        try:
            db.ping()
            break
        except:
            db.ping(True)
    #db.ping(reconnect=True) 
     
    # execute 执行SQL数据库语句
    cursor.execute(sql)
    # fetchall() 获得执行sql语句后获得的结果
    result = cursor.fetchall()
    # commit是把查询语句提交到数据库内，而不只是要向数据库提交增、添的数据。
    db.commit()
    
    #cursor.close()
    # 返回从数据库获取的结果
    return result

def db_file(sql):
    #lock = threading.Lock() 
    #lock.acquire()
    res = sqlquery(sql)
    #lock.release()
    return res