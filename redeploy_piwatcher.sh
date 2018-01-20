#!/bin/bash

ALL_HOSTS="osmc@osmc pi@pizero1 pi@pizero2 pi@pizero3 pi@banane"

# To allow sudo without password, add this to /etc/sudoers
# pi	ALL=NOPASSWD: /etc/init.d/piwatcher-daemon

HOSTS=$1
if [ -z $HOSTS ] ; then
    HOSTS="$ALL_HOSTS"
fi
echo "Running on HOSTS=$HOSTS"
for HOST in $HOSTS ; do
    echo "HOST $HOST"
cat << EOF | ssh -T $HOST
cd ~/git/piwatcher
git pull
sudo /etc/init.d/piwatcher-daemon restart
EOF
done
