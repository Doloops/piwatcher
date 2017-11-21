import piwatcherconfig
import cpuwatcher
import push2es

import sys
import time

class PiWatcher:
    pwConfig = piwatcherconfig.PiWatcherConfig.getConfig()
    
    piModules = []

    def __init__(self):    
        # Static definitions
        self.piModules.append(cpuwatcher.CpuWatcher())
        
        hostname = self.pwConfig["hostname"]
        self.updateInterval = self.pwConfig["stats"]["updateInterval"]
        self.statsInterval = self.pwConfig["stats"]["statsInterval"]
        
        if ("disk" in self.pwConfig) and self.pwConfig["disk"]["enabled"]:
            import diskwatcher
            self.piModules.append(diskwatcher.DiskWatcher(diskLedPinout=self.pwConfig["disk"]["ledPinout"], diskDeviceName=self.pwConfig["disk"]["deviceName"]))
        
        if "sensors" in self.pwConfig and self.pwConfig["sensors"]["bmp280"]["enabled"]:
            import tempwatcher
            self.piModules.append(tempwatcher.TempWatcher())
        
        if "fetchfromes" in self.pwConfig:
            import fetchfromes
            self.piModules.append(fetchfromes.FetchFromES(self.pwConfig["fetchfromes"]))
        
        if "piscript" in self.pwConfig:
            import piscript
            self.piModules.append(piscript.PiScript(self.pwConfig["piscript"]))
        
        if "picommander" in self.pwConfig:
            import picommandwatcher
            self.piModules.append(picommandwatcher.PiCommandWatcher(self.pwConfig["picommander"]))
        
        if "picurrentsensor" in self.pwConfig:
            import picurrentsensor
            self.piModules.append(picurrentsensor.PiCurrentSensor(self.pwConfig["picurrentsensor"]))
        
        self.piModules.append(push2es.Push2ES(
            hostname = hostname,
            statsInterval = self.pwConfig["stats"]["statsInterval"],
            moduleConfig = self.pwConfig["elastic"]))
            
        for module in self.piModules:
            print("* using module " + module.getModuleName())
            module.setPiWatcher(self)

    def run(self):    
        try:
            while True:
                loopstart = time.time()
                tnow = time.strftime("%Y%m%d-%H%M%S")
                print (tnow, end='')
                
                measure={"statsInterval": self.statsInterval}
                
                
                for module in self.piModules:
                    try:
                        module.update(measure)
                    except Exception as err:
                        print(" ! Caught " + str(err))
                        print("Could not update module " + module.getModuleName(), str(sys.exc_info()))
                        # raise err
                        break
        
                loopend = time.time()
                print(" {" + ("%.3f"%((loopend-loopstart)*1000)) + "}", end='')
                print(".")
                time.sleep(self.updateInterval)
        
        finally:
            for module in self.piModules:
                try:
                    module.shutdown()
                except:
                    print("Could not shutdown " + module.getModuleName(), sys.exc_info()[0])
    
    def updateModule(self, name, measure):
        for module in self.piModules:
            if module.getName() == name:
                module.update(measure)

if __name__ == "__main__":
    piwatcher = PiWatcher()
    piwatcher.run()
    