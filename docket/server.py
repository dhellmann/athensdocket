import calendar
import datetime
import functools
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, g, request, url_for
from flask.ext.pymongo import PyMongo, ASCENDING
from flask.ext.wtf import Form, StringField, SelectField, validators

from docket.encodings import ENCODERS

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'docket'
mongo = PyMongo(app)

# How short do we allow names for searching?
MIN_NAME_LENGTH = 3

# Turn off cross-site checking since we aren't saving user data
app.csrf_enabled = False


@app.template_filter('date')
def date(d):
    if d:
        return d.strftime('%Y-%m-%d')
    else:
        return ''


@app.template_filter('month')
def month(d):
    if d:
        return d.strftime('%B')
    else:
        return ''


@app.template_filter('sentence_amount')
def sentence_amount(s):
    if not s['amount']:
        return ''
    if s['units'] == '$':
        fmt = '$ %(amount)0.2f'
    else:
        fmt = '%(amount)d %(units)s'
    return fmt % s


@app.template_filter('participant_search_url')
def participant_search_url(p, encoding='normalized'):
    fn = p['first_name']
    ln = p['last_name']
    return url_for('search',
                   first_name=fn if len(fn) >= MIN_NAME_LENGTH else '',
                   last_name=ln if len(ln) >= MIN_NAME_LENGTH else '',
                   encoding=encoding,
                   )


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


def name_length_check(form, field):
    app.logger.debug('checking length of %s', field)
    if field.data and len(field.data) < MIN_NAME_LENGTH:
        raise validators.ValidationError(
            'Must be at least %s characters long' % MIN_NAME_LENGTH
            )

ENCODING_CHOICES = [('exact', 'Exact match'),
                    ('normalized', 'Ignore case'),
                    ('soundex', 'Soundex'),
                    ('metaphone', 'Metaphone'),
                    ('nysiis', 'NYSIIS'),
                    ]


class SearchForm(Form):
    first_name = StringField('First Name', [name_length_check])
    last_name = StringField('Last Name', [name_length_check])
    encoding = SelectField('Search Type',
                           default='normalize',
                           choices=ENCODING_CHOICES,
                           )


def make_encoded_expression(field, encoded):
    encoded = filter(bool, encoded)
    if len(encoded) == 1:
        return {field: encoded[0]}
    return {'$or': [{field: e} for e in encoded]}


def make_query_for_encoding(form, encoding):
    encoder = ENCODERS[encoding]
    q = {}
    if form.first_name.data:
        q.update(make_encoded_expression('first_name',
                                         encoder(form.first_name.data),
                                         )
                 )
    if form.last_name.data:
        q.update(make_encoded_expression('last_name',
                                         encoder(form.last_name.data),
                                         )
                 )
    if q:
        q['encoding'] = encoding
    return q


@app.route('/search')
@set_navbar_active
def search():
    results = []
    alternate_counts = []
    form = SearchForm(request.args, csrf_enabled=False)
    if form.validate():
        q = make_query_for_encoding(form, form.encoding.data)
        if q:
            app.logger.debug('query = %s', q)
            participants = mongo.db.participants
            results = participants.find(q, sort=[('date', ASCENDING)])
            alternate_counts = [
                {'encoding': display_name,
                 'count': participants.find(make_query_for_encoding(form, encoding_name)).count(),
                 'url': participant_search_url({'first_name': form.first_name.data,
                                                'last_name': form.last_name.data,
                                                },
                                               encoding_name),
                 }
                for encoding_name, display_name in ENCODING_CHOICES
                if encoding_name != form.encoding.data
                ]
            app.logger.debug('alternates: %r', alternate_counts)
    return render_template('search.html',
                           form=form,
                           results=results,
                           alternate_counts=alternate_counts,
                           )


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


@app.route('/case/<path:caseid>', methods=['GET'])
def case(caseid):
    case = mongo.db.cases.find_one({'_id': caseid})
    violation = mongo.db.violation_codes.find_one({'_id': case['violation']})
    cases_on_page = mongo.db.cases.find({'book': case['book'],
                                         'page': case['page'],
                                         },
                                        sort=[('_id', ASCENDING)],
                                        )
    job = mongo.db.jobs.find_one({'_id': case['load_job_id']})
    app.logger.debug('args: %r', request.args)
    user_debug = bool(request.args.get('debug', False))
    return render_template('case.html',
                           case=case,
                           violation=violation,
                           cases_on_page=cases_on_page,
                           debug=(app.debug or user_debug),
                           job=job,
                           )


@app.route('/code/<code>')
def code(code):
    violation = mongo.db.violation_codes.find_one({'_id': code})
    return render_template('code.html',
                           violation=violation,
                           )

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
