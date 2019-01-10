# piwatcher
The purpose of this project is to build an array of Raspberry Pi Zero nodes, equiped with BMP280 temperature sensors, for home automation.

These headless nodes collect (near) real-time temperature and pressure data, and push them to an ElasticSearch node.

Current status : **completely experimental !**

BMP280 i2c driver code comes from [SunFounder SensorKit](https://github.com/sunfounder/SunFounder_SensorKit_for_RPi2.git).

Thanks guys for this great work !

# Requirements and Installing
apt-get install python3-rpi.gpio python3-smbus python3-elasticsearch python3-redis
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


## /etc/piwatcher-daemon.config : piwatcher service daemon configuration

This config file only deals with running the daemon service properly.
Config values are pretty straightforward.

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

## BMP280/BME280 Temperature sensor
	
Temperature is pushed to stats:`$host.indoorTemp`, pressure is pushed to stats:`$host.indoorPressure`, humidity is push to stats: `$host.indoorHumidity` (BME280 only).

Configuration is done via the same module, called bmp280 or bme280.
For BME280 only, specify "model":"BME280" in the configuration.
	{
        "name":"bme280",
        "address":"0x77",
        "model":"BME280",
        "busnum":1, 
        "enabled": true
	}
Multiple addresses and multiple buses are supported as well.
Add a prefix value to distinguish between multiple sensors on the same node.


## Disk monitoring
Disk state is pushed to stats:`$host.diskState` and can take values `standby`, `idle` or `active`.
stats:`$host.cumulateDiskStateTime` counts the number of seconds the state did not change. That's a float with may too much precision ATM...

# Notes

## Multiple I2C Buses on Raspberry PI

Having multiple i2c buses on the same Raspberry PI *is* tricky !
The default hardware one is wired to PIN3(SDA) and PIN5(SCL).
Adding a new one, software driven via GPIO, can be easily achieved via /boot/config.txt such as :

dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=27,i2c_gpio_scl=22,i2c_gpio_delay_us=200

(See https://www.raspberrypi.org/forums/viewtopic.php?t=205576 for example).

*BUT* the PINs to provide are not the 40-PIN header pin numbers, but the BCM ones.
See https://raspberrypi.stackexchange.com/questions/12966/what-is-the-difference-between-board-and-bcm-for-gpio-pin-numbering !

And then comes the pull-out problem, especially for the SCL line.
This seems to depend on what is plugged into the i2c bus.

Adding a 1k5 Ohm between SCL and 3.3V lines solved issues, along with a great value for i2c_gpio_delay_us value.

