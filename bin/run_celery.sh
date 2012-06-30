#!/bin/sh

cd /home/docket/athensdocket

/home/docket/env/bin/celeryd -f /home/docket/logs/celery.log -l INFO --pidfile /home/docket/logs/celery.pid
