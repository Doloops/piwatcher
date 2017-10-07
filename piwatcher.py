import RPi.GPIO as GPIO ## Import GPIO library
from datetime import datetime
import time
import elasticsearch
import diskwatcher
import cpuwatcher
import bmp280
import sys
import json
from os.path import expanduser


def getConfig():
    with (open(expanduser("~") + "/.piwatcher/config.json")) as confFile:
        confString = confFile.read()
        return json.loads(confString)

pwConfig = getConfig()

print ("Start with config : " + str(pwConfig))

# Static definitions

cpuWatcher = cpuwatcher.CpuWatcher()

diskWatcher = None
if pwConfig["disk"]["enabled"]:
    diskWatcher = diskwatcher.DiskWatcher(diskLedPinout=pwConfig["disk"]["ledPinout"], diskDeviceName=pwConfig["disk"]["deviceName"])

hostname = pwConfig["hostname"]
updateInterval = pwConfig["stats"]["updateInterval"]
statsInterval = pwConfig["stats"]["statsInterval"]

es = elasticsearch.Elasticsearch(pwConfig["elastic"]["hosts"])
esIndex = pwConfig["elastic"]["index"]
esType = pwConfig["elastic"]["type"]
lastESUpdate = time.time()

tempSensorBmp280 = None
if pwConfig["sensors"]["bmp280"]["enabled"]:
    tempSensorBmp280 = bmp280.BMP280()
    chip_id, chip_version = tempSensorBmp280.read_id()

    if chip_id == 88:
	    tempSensorBmp280.reg_check()
    else:
        raise ValueError ("Unsupported chip : " + chip_id)

try:
    while True:
        now = time.time()

        esbody = {"timestamp": datetime.utcnow()}
        measure={"statsInterval": statsInterval}
        esbody[hostname] = measure

        measure["cpuTemp"] = cpuWatcher.getCPUTemp()
        measure["cpuLoad"] = cpuWatcher.getCPULoad()
        cpuMessage = ", cpuTemp=" + str(measure["cpuTemp"]) + ", load=" + str(measure["cpuLoad"])

        diskState = None
        diskStateTime = None
        diskStateMessage = ""
        if diskWatcher is not None:
            diskState = diskWatcher.checkDiskState()
            diskWatcher.setLedFromDiskState(diskState)
            previousDiskStateTime = diskWatcher.updateDiskStateTime(diskState)
            measure["diskState"] = diskState
            measure["cumulateDiskStateTime"] = now - previousDiskStateTime
            diskStateMessage = ", diskState=" + diskState + " for " + str(int(measure["cumulateDiskStateTime"])) + "s"

        tempSensorMessage = ""    
        if tempSensorBmp280 is not None:
            indoorTemp, indoorPressure = tempSensorBmp280.read()
            measure["indoorTemp"] = indoorTemp
            measure["indoorPressure"] = indoorPressure
            tempSensorMessage = ", temp=" + ("%2.2f'C" % indoorTemp) + ", pressure=" + ("%5.4f mbar" % indoorPressure)

        tnow = time.strftime("%Y%m%d-%H%M%S")
        print (tnow + diskStateMessage + cpuMessage + tempSensorMessage, end='')
        
        if ( now - lastESUpdate >= statsInterval ):
            try:
                tsBefore = time.time()
                es.index(index=esIndex, doc_type=esType, id=tnow, body=esbody)
                print (" * Indexed in " + ("%.3f s" % (time.time() - tsBefore)), end='')
                lastESUpdate = now
            except:
                print("Could not index to ES: ", sys.exc_info()[0])

        print(".")
        time.sleep(updateInterval)

finally:
    if diskWatcher is not None:
        diskWatcher.shutdown()

