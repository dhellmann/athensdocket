import urllib

from .app import app, mongo, MIN_NAME_LENGTH, MAX_SEARCH_HISTORY
from .filters import participant_search_url
from .nav import set_navbar_active
from ..encodings import ENCODERS

from flask import request, session, render_template
from flask.ext.pymongo import ASCENDING
from flask.ext.wtf import Form, StringField, SelectField, validators


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
ENCODING_CHOICE_DICT = dict(ENCODING_CHOICES)


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
    count = 0
    form = SearchForm(request.args, csrf_enabled=False)
    if form.validate():
        q = make_query_for_encoding(form, form.encoding.data)
        if q:
            app.logger.debug('query = %s', q)

            participants = mongo.db.participants
            results = participants.find(q, sort=[('date', ASCENDING)])
            count = results.count()
            alternate_counts = [
                {'encoding': display_name,
                 'count': participants.find(
                        make_query_for_encoding(form, encoding_name)
                        ).count(),
                 'url': participant_search_url(
                        {'first_name': form.first_name.data,
                         'last_name': form.last_name.data,
                         },
                        encoding_name),
                 }
                for encoding_name, display_name in ENCODING_CHOICES
                if encoding_name != form.encoding.data
                ]
            app.logger.debug('alternates: %r', alternate_counts)

            #session['search_history'] = []  # useful for clearing the history
            search_terms = dict((n, getattr(form, n).data)
                                for n in q.keys()
                                )
            display_terms = {}
            display_terms.update(search_terms)
            display_terms['encoding'] = ENCODING_CHOICE_DICT[search_terms['encoding']]
            history_entry = {
                'url': urllib.urlencode(search_terms),
                'terms': display_terms,
                'hits': count,
                }
            history = [h
                       for h in session.get('search_history', [])
                       if not h['url'] == history_entry['url']
                       ][:MAX_SEARCH_HISTORY - 1]
            history.insert(0, history_entry)
            session['search_history'] = history
            app.logger.debug('search history: %r',
                             session['search_history'])

    return render_template('search.html',
                           form=form,
                           results=results,
                           count=count,
                           alternate_counts=alternate_counts,
                           )
