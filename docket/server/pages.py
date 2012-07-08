from .app import app, mongo
from .nav import set_navbar_active

from flask import render_template


@app.route('/')
@set_navbar_active
def index():
    return render_template('index.html')


@app.route('/about')
@set_navbar_active
def about():
    return render_template('about.html')


@app.route('/code/<code>')
def code(code):
    violation = mongo.db.violation_codes.find_one({'_id': code})
    return render_template('code.html',
                           violation=violation,
                           )
