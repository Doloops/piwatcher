#!/bin/bash

# Script to deploy as a service from the git/piwatcher folder
# Meant to be run as a sudoer, not as root.
HOST=$1
USER=$(whoami)

if [ -z $HOST ] ; then
    echo "You must provide at least one argument : HOST"
    exit 1
fi

echo "Installing PIWatcher for HOST=$HOST"
SRC=/home/$USER/git/piwatcher

CONF=$SRC/confs/$HOST/config.json
TARGET_CONF=~/.piwatcher/config.json
echo "Installing PIWatcher configuration $CONF"
if [ -a $TARGET_CONF ] ; then
    echo "Removing previous conf $TARGET_CONF"
    rm $TARGET_CONF
fi
if [ ! -d ~/.piwatcher ] ; then
    mkdir ~/.piwatcher
fi
echo "Linking conf file ..."
ln -sv $CONF $TARGET_CONF

echo "Installing piwatcher-daemon service"

TARGET_SERVICE=/etc/init.d/piwatcher-daemon
if [ -a $TARGET_SERVICE ] ; then
    echo "Removing target service $TARGET_SERVICE"
    sudo rm $TARGET_SERVICE
fi
echo "Linking daemon service ..."
sudo ln -sv $SRC/piwatcher-daemon.sh $TARGET_SERVICE

TARGET_SERVICE_CONF=/etc/piwatcher-daemon.conf
if [ -a $TARGET_SERVICE_CONF ] ; then
    echo "Removing target service $TARGET_SERVICE_CONF"
    sudo rm $TARGET_SERVICE_CONF
fi
echo "Linking daemon conf file"
sudo ln -sv $SRC/piwatcher-daemon.conf $TARGET_SERVICE_CONF

sudo update-rc.d piwatcher-daemon defaults
