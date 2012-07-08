from .app import app, MIN_NAME_LENGTH

from flask import url_for


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
