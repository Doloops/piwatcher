import RPi.GPIO as GPIO ## Import GPIO library
import time
import diskwatcher
import cpuwatcher
import tempwatcher
import push2es

import sys
import json
from os.path import expanduser


def getConfig():
    with (open(expanduser("~") + "/.piwatcher/config.json")) as confFile:
        confString = confFile.read()
        return json.loads(confString)

pwConfig = getConfig()

print ("Start with config : " + str(pwConfig))

piModules = []

# Static definitions
piModules.append(cpuwatcher.CpuWatcher())

hostname = pwConfig["hostname"]
updateInterval = pwConfig["stats"]["updateInterval"]
statsInterval = pwConfig["stats"]["statsInterval"]

diskWatcher = None
if pwConfig["disk"]["enabled"]:
    piModules.append(diskwatcher.DiskWatcher(diskLedPinout=pwConfig["disk"]["ledPinout"], diskDeviceName=pwConfig["disk"]["deviceName"]))

if pwConfig["sensors"]["bmp280"]["enabled"]:
    piModules.append(tempwatcher.TempWatcher())

piModules.append(push2es.Push2ES(
    hosts = pwConfig["elastic"]["hosts"], 
    hostname = hostname,
    esIndex = pwConfig["elastic"]["index"], 
    esType =  pwConfig["elastic"]["type"],
    statsInterval = pwConfig["stats"]["statsInterval"]))
    
for module in piModules:
    print("* using module " + module.getModuleName())

try:
    while True:
        tnow = time.strftime("%Y%m%d-%H%M%S")
        print (tnow, end='')
        
        measure={"statsInterval": statsInterval}
        
        for module in piModules:
            module.update(measure)

#        if cpuWatcher is not None:
#            cpuWatcher.update(measure)

#        if diskWatcher is not None:
#            diskWatcher.update(measure)

#        if tempSensorBmp280 is not None:
#            try:
#                tempSensorBmp280.update(measure)
#            except:
#                print("Could not get BMP280 sensor information : ", sys.exc_info()[0])
#                time.sleep(updateInterval)
#                continue



        print(".")
        time.sleep(updateInterval)

finally:
    for module in piModules:
        try:
            module.shutdown()
        except:
            print("Could not shutdown " + module.getModuleName(), sys.exc_info()[0])

