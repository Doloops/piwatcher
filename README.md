# piwatcher
The purpose of this project is to build an array of Raspberry Pi Zero nodes, equiped with BMP280 temperature sensors, for home automation.

These headless nodes collect (near) real-time temperature and pressure data, and push them to an ElasticSearch node.

Current status : **completely experimental !**

BMP280 i2c driver code comes from [SunFounder SensorKit](https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2.git).

Thanks guys for this great work !

# Requirements and Installing
apt-get install python3-rpi.gpio python3-smbus python3-elasticsearch
modprobe i2c_dev

python3-daemonize may be helpfull in the future...

The install.sh script is a convenient way to deploy what's required, with all nodes keeping their configurations under git as well.

Still having trouble finding out the 'python3' way to deploy packages on the system (aka applications and services), all the code remains in the ~/git/piwatcher directory at the moment (that may change).

Note that accessing i2c bus requires root privilege by default, so piwatcher is run as root here (there may be special tricks to do so, didn't spend time on it yet).

# Configuring
Two configuration files are required :
## ~/piwatcher/config.json : piwatcher configuration itself

Most of the piwatcher behavior can be setup in this JSON-formatted config file.
See examples in `confs/*` to see how it can be set up.

    {
        "hostname" : "osmc",
        "disk": {
            "enabled": true,
            "ledPinout": 11,
            "deviceName": "sda"
        },
        "sensors" : {
            "bmp280" : {
                "enabled": true
            }
        },
        "elastic" : {
            "hosts":[{"host" : "osmc"}],
            "index": "oswh-osmc",
            "type": "sys-measure"
        },
        "stats" : {
            "updateInterval" : 2,
            "statsInterval" : 60
        }
    }


# Features

Notation :

* All conf:`setting.setting` code refers to configuration settings, see Configuring.
* All stats:`$host.stats` code refers to information pushed to ElasticSearch.

## General behavior
Basically, piwatcher will loop each conf:`stats.updateInterval` seconds and retrieve information.
Each conf:`stats.statsInterval`, it will push this information to ElasticSearch.

## CPU monitoring
Monitoring load (aka /proc/loadavg), taking the last-minute value, and pushing it into stats:`$host.cpuLoad`.
CPU temperature is pushed to stats:`$host.cpuTemp`.

## BMP280 Temperature sensor
Temperature is pushed to stats:`$host.indoorTemp`, pressured is pushed to stats:`$host.indoorPressure`

## Disk monitoring
Disk state is pushed to stats:`$host.diskState` and can take values `standby`, `idle` or `active`.
stats:`$host.cumulateDiskStateTime` counts the number of seconds the state did not change. That's a float with may too much precision ATM...


## /etc/piwatcher-daemon.config : piwatcher service daemon configuration

This config file only deals with running the daemon service properly.
Config values are pretty straightforward.

