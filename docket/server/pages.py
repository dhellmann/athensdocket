from .app import app
from .nav import set_navbar_active

from flask import render_template


@app.route('/')
@set_navbar_active
def index():
    return render_template('index.html')
