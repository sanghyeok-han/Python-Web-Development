from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)

app.config["SECRET_KEY"] = '1d4ffc4a4ae5555e88058e0d'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.init_app(app)

login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.login_message = u"로그인이 필요한 서비스입니다."

from healthton import routes