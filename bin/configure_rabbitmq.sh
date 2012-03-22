#!/bin/sh

rabbitmqctl add_user docket docket
rabbitmqctl add_vhost dockethost
rabbitmqctl set_permissions -p dockethost docket ".*" ".*" ".*"