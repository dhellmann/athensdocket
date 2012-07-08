import os
import sys

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, app_dir)

from docket.server.app import app

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
