import os

from flask import Flask
from flask.ext.pymongo import PyMongo

# Where are we running?
app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

app = Flask(__name__)

try:
    with open(os.path.join(app_dir, 'session-secret.txt'), 'rt') as f:
        key = f.read()
except (IOError, OSError):
    key = 'not-very-secret'
app.config['SECRET_KEY'] = key

app.config['MONGO_DBNAME'] = 'docket'
mongo = PyMongo(app)

# How short do we allow names for searching?
MIN_NAME_LENGTH = 3

# How much search history should we keep?
MAX_SEARCH_HISTORY = 10
