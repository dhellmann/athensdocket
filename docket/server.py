import calendar
import datetime
import functools

from flask import Flask, render_template, g
from flask.ext.pymongo import PyMongo, ASCENDING

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'docket'
mongo = PyMongo(app)


@app.template_filter('date')
def date(d):
    return d.strftime('%Y-%m-%d')


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


@app.route('/browse/date/<int:year>')
@app.route('/browse/date/<int:year>/<int:month>')
@app.route('/browse/date/<int:year>/<int:month>/<int:day>')
def browse_date(year, month=None, day=None):
    g.navbar_active = 'browse'
    if month and day:
        first_day = datetime.datetime(year, month, day, 0, 0, 0)
        last_day = first_day + datetime.timedelta(days=1)
        date_range = date(first_day)
    elif month:
        first_day = datetime.datetime(year, month, 1, 0, 0, 0)
        weekday, num_days = calendar.monthrange(year, month)
        last_day = first_day + datetime.timedelta(days=num_days)
        date_range = '%s-%02d' % (year, month)
    elif year:
        first_day = datetime.datetime(year, 1, 1, 0, 0, 0)
        last_day = datetime.datetime(year + 1, 1, 1, 0, 0, 0)
        date_range = unicode(year)
    else:
        raise ValueError('Invalid date')
    app.logger.debug('first_day=%s, last_day=%s', first_day, last_day)
    cases = mongo.db.cases.find({'arrest_date': {'$gte': first_day,
                                                 '$lt': last_day,
                                                 },
                                 },
                                sort=[('arrest_date', ASCENDING)],
                                )
    return render_template('browse_date.html',
                           date_range=date_range,
                           cases=cases,
                           year=year,
                           month=month,
                           day=day,
                           )


@app.route('/case/<path:caseid>')
def case(caseid):
    case = mongo.db.cases.find_one({'_id': caseid})
    return render_template('case.html',
                           case=case,
                           )


@app.route('/code/<code>')
def code(code):
    violation = mongo.db.violation_codes.find_one({'_id': code})
    return render_template('code.html',
                           violation=violation,
                           )

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
