import functools

from flask import Flask, render_template, g

app = Flask(__name__)


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

if __name__ == '__main__':
    app.run(debug=True)
