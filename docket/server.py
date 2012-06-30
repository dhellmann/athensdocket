import functools
import operator

from flask import Flask, render_template, g
from flask.ext.pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'docket'
mongo = PyMongo(app)


def set_navbar_active(f):
    "Set the navbar active value to the name of the wrapped function."
    @functools.wraps(f)
    def set_active(*args, **kwds):
        g.navbar_active = f.__name__
        return f(*args, **kwds)
    return set_active


@app.route('/')
@set_navbar_active
def index():
    return render_template('index.html')


@app.route('/about')
@set_navbar_active
def about():
    return render_template('about.html')


@app.route('/search')
@set_navbar_active
def search():
    return render_template('search.html')


@app.route('/browse')
@set_navbar_active
def browse():
    books = mongo.db.books.find()
    years = sorted(set(b['year'] for b in books))

    violations = sorted(mongo.db.violation_codes.find(),
                        key=operator.itemgetter('code'),
                        )

    return render_template('browse.html',
                           years=years,
                           violations=violations,
                           )

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
