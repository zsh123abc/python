from flask import Flask
from config import config
import os
from views import *
from model import pools

app = Flask(__name__)
pool = pools()
#env = os.getenv('FLASK_ENV', 'development') # 从环境配置文件获取当前环境
#app.config.from_object(config.get(env, 'default'))
##db = SQLAlchemy(app)
#import models