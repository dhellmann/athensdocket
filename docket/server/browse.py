import calendar
import datetime

from .app import app, mongo
from .filters import date
from .nav import set_navbar_active

from flask import render_template, g
from flask.ext.pymongo import ASCENDING


@app.route('/browse')
@set_navbar_active
def browse():
    books = mongo.db.books.find()
    years = sorted(set(b['year'] for b in books))
    locations = sorted(mongo.db.cases.distinct('location'))
    return render_template('browse.html',
                           years=years,
                           locations=locations,
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
    cases = mongo.db.cases.find({'date': {'$gte': first_day,
                                          '$lt': last_day,
                                          },
                                 },
                                sort=[('date', ASCENDING)],
                                )
    return render_template('browse_date.html',
                           date_range=date_range,
                           cases=cases,
                           year=year,
                           month=month,
                           day=day,
                           )


@app.route('/browse/location/<location>')
def browse_location(location):
    cases = mongo.db.cases.find({'location': location,
                                 },
                                sort=[('date', ASCENDING)],
                                )
    return render_template('browse_location.html',
                           location=location,
                           cases=cases,
                           )
