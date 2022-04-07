from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
from config import config
import os
from views import *

app = Flask(__name__)

#env = os.getenv('FLASK_ENV', 'development') # 从环境配置文件获取当前环境
#app.config.from_object(config.get(env, 'default'))
##db = SQLAlchemy(app)
#import models