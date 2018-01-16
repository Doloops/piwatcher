from piwatcher import piwatcherconfig
from piwatcher import pimodule

import sys
import time
import math

class PiWatcher:
    pwConfig = piwatcherconfig.getPiWatcherConfig()

    aliases = {"cpu":"cpuwatcher", "disk":"diskwatcher", "elastic":"push2es", "bmp280":"tempwatcher", 
               "piscript": "piscript", "picommander":"picommandwatcher", "picurrentsensor": "picurrentsensor"}
    
    piModules = []
    updateInterval = None

    def __init__(self):    
        self.updateInterval = self.pwConfig["updateInterval"]
        for moduleConfig in self.pwConfig["modules"]:
            if moduleConfig["name"] is None:
                raise ValueError("No moduleConfig name found for " + str(moduleConfig))
            self.__initModule(moduleConfig)

        for module in self.piModules:
            print("* Using module " + module.getModuleName() + ", class=" + module.getModuleClassName())
            module.setPiWatcher(self)

    def __initModule(self, moduleConfig):
        moduleName = self.aliases[moduleConfig["name"]]
        print("Importing : " + moduleName)
#        exec ("from piwatcher import " + moduleName)
        moduleInstance = self.__instantiateModule("piwatcher." + moduleName, moduleConfig)
        moduleInstance.setPiWatcher(self)
        self.piModules.append(moduleInstance)

    def __instantiateModule(self, moduleName, moduleConfig):
        exec ("import " + moduleName)
        current_module = sys.modules[moduleName]
        for key in dir(current_module):
            attr = getattr(current_module, key)
            if isinstance( attr, type ):
                # print("This is a class " + moduleName + "." + key + " : " + str(attr))
                if issubclass(attr, pimodule.PiModule):
                    print("This is a module class : " + str(attr))
                    moduleInstance = attr(moduleConfig)
                    print("=> New module instance : " + str(moduleInstance))
                    return moduleInstance
        raise ValueError("Could not instantiate " + moduleName)

    def __print_classes(self, name = __name__):
        current_module = sys.modules[name]
        print("current_module=" + str(current_module))
        for key in dir(current_module):
            print("key " + str(key))
            if isinstance( getattr(current_module, key), type ):
                print(key)

    def __legacy_init__(self):
        # Static definitions
        from piwatcher import cpuwatcher
        self.piModules.append(cpuwatcher.CpuWatcher())

        hostname = self.pwConfig["hostname"]
        self.updateInterval = self.pwConfig["stats"]["updateInterval"]
        self.statsInterval = self.pwConfig["stats"]["statsInterval"]
        
        if ("disk" in self.pwConfig) and self.pwConfig["disk"]["enabled"]:
            from piwatcher import diskwatcher
            self.piModules.append(diskwatcher.DiskWatcher(diskLedPinout=self.pwConfig["disk"]["ledPinout"], diskDeviceName=self.pwConfig["disk"]["deviceName"]))
        
        if "sensors" in self.pwConfig and self.pwConfig["sensors"]["bmp280"]["enabled"]:
            from piwatcher import tempwatcher
            self.piModules.append(tempwatcher.TempWatcher())
            # This is dirty and must be retought entirely
            if "secondSensor" in self.pwConfig["sensors"]["bmp280"]:
                secondSensorConfig = self.pwConfig["sensors"]["bmp280"]["secondSensor"]
                self.piModules.append(tempwatcher.TempWatcher(prefix = secondSensorConfig["prefix"], address=secondSensorConfig["address"]))
        
        if "fetchfromes" in self.pwConfig:
            from piwatcher import fetchfromes
            self.piModules.append(fetchfromes.FetchFromES(self.pwConfig["fetchfromes"]))
        
        if "piscript" in self.pwConfig:
            from piwatcher import piscript
            self.piModules.append(piscript.PiScript(self.pwConfig["piscript"]))
        
        if "picommander" in self.pwConfig:
            from piwatcher import picommandwatcher
            self.piModules.append(picommandwatcher.PiCommandWatcher(self.pwConfig["picommander"]))
        
        if "picurrentsensor" in self.pwConfig:
            from piwatcher import picurrentsensor
            self.piModules.append(picurrentsensor.PiCurrentSensor(self.pwConfig["picurrentsensor"]))
        
        from piwatcher import push2es
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
                
                # measure={"statsInterval": self.statsInterval}
                measure = {}
                
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
                time.sleep(math.fabs(self.updateInterval - loopend))
        
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
