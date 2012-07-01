import datetime
import functools

from flask import Flask, render_template, g
from flask.ext.pymongo import PyMongo, ASCENDING

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
    violations = mongo.db.violation_codes.find(sort=[('code', ASCENDING)])
    return render_template('browse.html',
                           years=years,
                           violations=violations,
                           )


@app.route('/browse/year/<int:year>')
def browse_year(year):
    g.navbar_active = 'browse'
    first_day = datetime.datetime(year, 1, 1, 0, 0, 0)
    last_day = datetime.datetime(year + 1, 1, 1, 0, 0, 0)
    cases = mongo.db.cases.find({'arrest_date': {'$gte': first_day,
                                                 '$lt': last_day,
                                                 },
                                 },
                                sort=[('arrest_date', ASCENDING)],
                                )
    return render_template('browse_year.html',
                           year=year,
                           cases=cases,
                           )


@app.route('/case/<path:caseid>')
def case(caseid):
    case = mongo.db.cases.find_one({'_id': caseid})
    return render_template('case.html',
                           case=case,
                           )

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
