from .app import app, mongo
from .nav import set_navbar_active

from flask import render_template
from flask.ext.pymongo import ASCENDING


@app.route('/about')
@set_navbar_active
def about():
    violations = mongo.db.violation_codes.find(sort=[('code', ASCENDING)])
    return render_template('about.html',
                           violations=violations,
                           )


@app.route('/about/code/<code>')
def code(code):
    violation = mongo.db.violation_codes.find_one({'_id': code})
    return render_template('code.html',
                           violation=violation,
                           )
