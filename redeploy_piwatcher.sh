#!/bin/bash

HOSTS="osmc@osmc pi@pizero1 pi@pizero2 pi@pizero3"
# HOSTS="pi@pizero1"

for HOST in $HOSTS ; do
    echo "HOST $HOST"
cat << EOF | ssh -T $HOST
cd ~/git/piwatcher
git pull
sudo /etc/init.d/piwatcher-daemon restart
EOF
done
