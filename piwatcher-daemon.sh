#!/bin/bash
# Mostly generic Daemon
# Sample script taken from http://werxltd.com/wp/2012/01/05/simple-init-d-script-template (Thanks !)
#
# chkconfig: 345 20 80
# description: PIWatcher Daemon
# processname: piwatcher

. /etc/piwatcher-daemon.conf

if [ -z $DAEMON_EXEC ] ; then
    $DAEMON_EXEC=$DAEMON
fi

case "$1" in
start)
	printf "%-50s" "Starting $NAME..."
	if [ -n $DAEMON_PATH ]; then
    	cd $DAEMON_PATH
    fi
	PID=`$DAEMON_EXEC $DAEMONOPTS > $LOGFILE 2>&1 & echo $!`
	echo "Saving PID" $PID " to " $PIDFILE
    if [ -z $PID ]; then
        printf "%s\n" "Fail"
    else
        echo $PID > $PIDFILE
        printf "%s\n" "Ok"
    fi
;;
status)
    printf "%-50s" "Checking $NAME..."
    if [ -f $PIDFILE ]; then
        PID=`cat $PIDFILE`
        if [ -z "`ps axf | grep ${PID} | grep -v grep`" ]; then
            printf "%s\n" "Process dead but pidfile exists"
        else
            echo "Running"
        fi
    else
        printf "%s\n" "Service not running"
    fi
;;
stop)
    printf "%-50s" "Stopping $NAME"
    PID=`cat $PIDFILE`
    if [ -n $DAEMON_PATH ]; then
        cd $DAEMON_PATH
    fi
    if [ -f $PIDFILE ]; then
        kill -HUP $PID
        printf "%s\n" "Ok"
        rm -f $PIDFILE
    else
        printf "%s\n" "pidfile not found"
    fi
;;

restart)
  	$0 stop
  	$0 start
;;

*)
    echo "Usage: $0 {status|start|stop|restart}"
    exit 1
esac
