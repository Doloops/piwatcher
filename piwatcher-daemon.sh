#!/bin/bash
# Mostly generic Daemon for PIWatcher
#
### BEGIN INIT INFO
# Provides:          piwatcher
# Required-Start:    $remote_fs $syslog $time
# Required-Stop:     $remote_fs $syslog $time
# Should-Start:      $network $named slapd autofs ypbind nscd nslcd winbind
# Should-Stop:       $network $named slapd autofs ypbind nscd nslcd winbind
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: PIWatcher monitors cpu, temps and disk activity
# Description:       PIWatcher monitors cpu, temps and disk activity
### END INIT INFO


# description: PIWatcher Daemon
# processname: piwatcher
# Sample script taken from http://werxltd.com/wp/2012/01/05/simple-init-d-script-template (Thanks !)

. /etc/piwatcher-daemon.conf

if [ -z $DAEMON_EXEC ] ; then
    $DAEMON_EXEC=$DAEMON
fi

case "$1" in
start)
    printf "%-50s" "Starting $NAME..."
    if [ -f $PIDFILE ]; then
        PID=`cat $PIDFILE`
        if [ -z "`ps axf | grep ${PID} | grep -v grep`" ]; then
            printf "%s\n" "Process dead but pidfile exists"
            rm -f $PIDFILE
        else
            echo "Daemon $DAEMON already running !"
            exit 1
        fi
    fi
    if [ -n $DAEMON_PATH ]; then
        cd $DAEMON_PATH
    fi
    PID=`$DAEMON_EXEC $DAEMON_OPTS > $LOGFILE 2>&1 & echo $!`
    # echo "Saving PID" $PID " to " $PIDFILE
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
