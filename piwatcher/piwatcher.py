from piwatcher import piwatcherconfig
from piwatcher import pimodule

import sys
import time
import math

class PiWatcher:
    pwConfig = piwatcherconfig.getPiWatcherConfig()

    aliases = {"cpu":"cpuwatcher", "disk":"diskwatcher", "elastic":"push2es", "bmp280":"tempwatcher", "bme280":"tempwatcher",
               "piscript": "piscript", "picommander":"picommandwatcher", "picurrentsensor": "picurrentsensor",
               "pidigitalsensor": "pidigitalsensor"}

    piModules = []
    updateInterval = None

    def __init__(self):
        self.updateInterval = self.pwConfig["updateInterval"]
        for moduleConfig in self.pwConfig["modules"]:
            if moduleConfig["name"] is None:
                raise ValueError("No moduleConfig name found for " + str(moduleConfig))
            if "enabled" in moduleConfig and moduleConfig["enabled"] == False:
                print("* Disabled module " + moduleConfig["name"])
                continue
            self.__initModule(moduleConfig)

        for module in self.piModules:
            print("* Using module name=" + module.getName() + ", module=" + module.getModuleName() + ", class=" + module.getModuleClassName())
            module.setPiWatcher(self)

    def __initModule(self, moduleConfig):
        if "module" in moduleConfig:
            moduleName = self.aliases[moduleConfig["module"]]
        else:
            moduleName = self.aliases[moduleConfig["name"]]

        moduleInstance = self.__instantiateModule("piwatcher." + moduleName, moduleConfig)
        moduleInstance.setPiWatcher(self)
        moduleInstance.setName(moduleConfig["name"])
        self.piModules.append(moduleInstance)

    def __instantiateModule(self, moduleName, moduleConfig):
        exec ("import " + moduleName)
        current_module = sys.modules[moduleName]
        for key in dir(current_module):
            attr = getattr(current_module, key)
            if isinstance( attr, type ):
                if issubclass(attr, pimodule.PiModule):
                    moduleInstance = attr(moduleConfig)
                    return moduleInstance
        raise ValueError("Could not instantiate " + moduleName)

    def __print_classes(self, name = __name__):
        current_module = sys.modules[name]
        print("current_module=" + str(current_module))
        for key in dir(current_module):
            print("key " + str(key))
            if isinstance( getattr(current_module, key), type ):
                print(key)

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
                looptime = loopend - loopstart
                print(" {" + ("%.3f"%((looptime)*1000)) + "}", end='')
                print(".")
                time.sleep(math.fabs(self.updateInterval - looptime))

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
                # This occurs out of band, so we have to add a line terminator for proper logs
                print(".")
