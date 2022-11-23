import pymysql
import threading
from DBUtils.PooledDB import PooledDB

class pools():
    # 初始化函数
    def __init__(self):
        self.pool = self.mysql_connection()

    def get_connect(self):
        if self.pool:
            # 连接数据库
            conn = self.pool.connection()
            
        return conn
    # print(th, '链接被拿走了', conn1._con)
    # print(th, '池子里目前有', pool._idle_cache, '\r\n')

    # 接口 sql语句操作
    def sqlquery(self,sql):
        conn = self.get_connect()
        # 创建游标
        cur = conn.cursor(pymysql.cursors.DictCursor)
        # 执行sql语句
        cur.execute(sql)
        # 获取全部数据
        result = cur.fetchall()
        # rollback 回滚，出现错误时可以回到刚开始的状态
        # 数据库增删改需要commit，提交事务，查询不需要
        conn.commit()
        # 关闭数据库连接
        cur.close()
        conn.close()
        # 返回从数据库获取到的全部数据
        return result

    # 数据库连接
    def mysql_connection(self):
        maxconnections = 20
        # pool 数据库连接池对象
        pool = PooledDB(
            # creator：数据库驱动模块，数据库类型
            pymysql,
            # maxconnections 被允许的最大连接数，
            # 默认0或None表示没有连接限制
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
    from app import pool
    return pool.sqlquery(sql)