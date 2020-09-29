import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# create app login manager and db
app = Flask(__name__)
login_manager = LoginManager()
db = SQLAlchemy()

# import blueprints, NOTE must be after above object creations
from . import general
from . import robot_interaction as robot
from . import auth

def create_app(robot_instance):
    app.config['SECRET_KEY'] = 'mysecretkey'
    app.config['ROBOT'] = robot_instance
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Connect db to app
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    db.init_app(app)
    Migrate(app,db)

    # Pass info from app to the login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Load our blueprints
    app.register_blueprint(robot.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(general.bp)
    app.add_url_rule('/', endpoint='index')
    return app
