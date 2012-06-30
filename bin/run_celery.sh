#!/bin/bash

cd /home/docket/athensdocket

LOGDIR=/home/docket/logs
PIDFILE=$LOGDIR/celery.pid

mkdir -p $LOGDIR

if [ -f $PIDFILE ]
then
	kill $(cat $PIDFILE)
	wait $(cat $PIDFILE)
	rm -f $PIDFILE
fi

nohup /home/docket/env/bin/celeryd -f $LOGDIR/celery.log -l INFO --pidfile $PIDFILE &
