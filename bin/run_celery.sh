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
		ps -elf | grep celery
		sleep 10
	fi
fi

# Move directories so we can find the docket code and celery config
# file
cd /home/docket/athensdocket

# Start the daemon
nohup /home/docket/env/bin/celeryd -f $LOGDIR/celery.log -l INFO --pidfile $PIDFILE &

for i in 1 2 3 4 5
do
	if [ ! -f $PIDFILE ]
	then
		echo "waiting..."
		sleep 10
	else
		echo "Running $(cat $PIDFILE)"
		break
	fi
done

