#!/bin/sh

export PATH=$PATH:/usr/local/sbin

#rabbitmqctl stop # just in case
#rabbitmq-server -detached

rabbitmqctl status
celeryd -l INFO 
#-f `pwd`/logs/celeryd.log
