from flask import Flask
from config import config
import os
from views import *
from model import pools

import logging
from logging.handlers import RotatingFileHandler
from config import BaseConfig



# 设置日志的记录等级
logging.basicConfig(level=BaseConfig.level) # 调试debug级
# 创建日志记录器，指明日志保存的路径（前面的logs为文件的名字，需要我们手动创建，后面则会自动创建）、每个日志文
#件的最大大小、保存的日志文件个数上限。
file_log_handler = RotatingFileHandler("../logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式               日志等级    输入日志信息的文件名   行数       日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


# from flask import current_app
# current_app.logger.error(e)

app = Flask(__name__)
pool = pools()
#env = os.getenv('FLASK_ENV', 'development') # 从环境配置文件获取当前环境
#app.config.from_object(config.get(env, 'default'))
##db = SQLAlchemy(app)
#import models