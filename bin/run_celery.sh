#!/bin/bash

cd /home/docket/athensdocket

LOGDIR=/home/docket/logs
PIDFILE=$LOGDIR/celery.pid

mkdir -p $LOGDIR

if [ -f $PIDFILE ]
then
	pid=$(cat $PIDFILE)
	if [ ! -z "$pid" ]
	then
		echo "Trying to kill $pid"
		kill $pid
	fi
	rm -f $PIDFILE
fi

nohup /home/docket/env/bin/celeryd -f $LOGDIR/celery.log -l INFO --pidfile $PIDFILE &
echo "Running $(cat $PIDFILE)"
