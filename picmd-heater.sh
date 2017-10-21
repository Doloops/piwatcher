#!/bin/bash

STATE=$1

if [ -z $STATE ] ; then
    echo "Must provide a valid state !"
    exit
fi


echo Setting heater to $STATE

# python3 picommander.py oswh-pizero1-cmd heaterCommand state $STATE

curl -XPUT 'osmc:9200/oswh-commands/command/pizero1-heater' -d"{\"state\":\"$STATE\"}"


