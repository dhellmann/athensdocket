#!/usr/bin/env python

# Enable the virtualenv
activate_this = '/home/docket/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# Load the application
from docket.server import app as application
