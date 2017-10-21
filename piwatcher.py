import piwatcherconfig
import diskwatcher
import cpuwatcher
import tempwatcher
import push2es
import picommandwatcher

import sys
import time

pwConfig = piwatcherconfig.PiWatcherConfig.getConfig()

piModules = []

# Static definitions
piModules.append(cpuwatcher.CpuWatcher())

hostname = pwConfig["hostname"]
updateInterval = pwConfig["stats"]["updateInterval"]
statsInterval = pwConfig["stats"]["statsInterval"]

diskWatcher = None
if ("disk" in pwConfig) and pwConfig["disk"]["enabled"]:
    piModules.append(diskwatcher.DiskWatcher(diskLedPinout=pwConfig["disk"]["ledPinout"], diskDeviceName=pwConfig["disk"]["deviceName"]))

if pwConfig["sensors"]["bmp280"]["enabled"]:
    piModules.append(tempwatcher.TempWatcher())


if "picommander" in pwConfig:    
    piModules.append(picommandwatcher.PiCommandWatcher(
        hosts = pwConfig["picommander"]["hosts"], 
        hostname = hostname,
        esIndex = pwConfig["picommander"]["index"], 
        esType = pwConfig["picommander"]["type"],
        esId = pwConfig["picommander"]["id"],
        esPropertyName = pwConfig["picommander"]["property"],
        esPropertyDefaultValue = pwConfig["picommander"]["defaultValue"],        
        channels = pwConfig["picommander"]["channels"],
        commands = pwConfig["picommander"]["commands"]
        ))


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
            try:
                module.update(measure)
            except Exception as err:
                print("! " + str(err))
                print("Could not update module " + module.getModuleName(), sys.exc_info()[0])
                # raise err
                break

        print(".")
        time.sleep(updateInterval)

finally:
    for module in piModules:
        try:
            module.shutdown()
        except:
            print("Could not shutdown " + module.getModuleName(), sys.exc_info()[0])

