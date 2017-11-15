import piwatcherconfig
import diskwatcher
import cpuwatcher
import tempwatcher
import push2es
import picommandwatcher
import piscript
import fetchfromes
import picurrentsensor

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


if "fetchfromes" in pwConfig:
    piModules.append(fetchfromes.FetchFromES(pwConfig["fetchfromes"]))

if "piscript" in pwConfig:
    piModules.append(piscript.PiScript(pwConfig["piscript"]))

if "picommander" in pwConfig:    
    piModules.append(picommandwatcher.PiCommandWatcher(pwConfig["picommander"]))

if "picurrentsensor" in pwConfig:
    piModules.append(picurrentsensor.PiCurrentSensor(pwConfig["picurrentsensor"]))

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
        loopstart = time.time()
        tnow = time.strftime("%Y%m%d-%H%M%S")
        print (tnow, end='')
        
        measure={"statsInterval": statsInterval}
        
        
        for module in piModules:
            try:
#                start = time.time()
                module.update(measure)
#                end = time.time()
#                print("{" + ("%.3f"%((end-start)*1000)) + "}", end='')
            except Exception as err:
                print(" ! Caught " + str(err))
                print("Could not update module " + module.getModuleName(), sys.exc_info()[0])
                # raise err
                break

        loopend = time.time()
        print(" {" + ("%.3f"%((loopend-loopstart)*1000)) + "}", end='')
        print(".")
        time.sleep(updateInterval)

finally:
    for module in piModules:
        try:
            module.shutdown()
        except:
            print("Could not shutdown " + module.getModuleName(), sys.exc_info()[0])

