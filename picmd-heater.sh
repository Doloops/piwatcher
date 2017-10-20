#!/bin/bash

STATE=$1

if [ -z $STATE ] ; then
    echo "Must provide a valid state !"
    exit
fi


echo Setting heater to $STATE

python3 picommander.py oswh-pizero1-cmd heaterCommand state $STATE

