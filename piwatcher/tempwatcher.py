'''
Utility class to monitor temperatures
'''

from piwatcher import pimodule
from piwatcher import bmp280

class TempWatcher(pimodule.PiModule):
    tempSensorBmp280 = None
    prefix = None
    address = 0x77
    
    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"Temp")
        if "address" in moduleConfig and moduleConfig["address"] == "0x76":
            self.address = 0x76
        if "prefix" in moduleConfig:
            self.prefix = moduleConfig["prefix"]
        self.tempSensorBmp280 = bmp280.BMP280(address=self.address)
        chip_id, chip_version = self.tempSensorBmp280.read_id()

        if chip_id == 88:
	        self.tempSensorBmp280.reg_check()
        else:
            raise ValueError ("Unsupported chip : " + chip_id + ", " + chip_version)

    def update(self, measure):
        indoorTemp, indoorPressure = self.tempSensorBmp280.read()
        # Guard against absurd values
        if indoorPressure < 920.0:
            raise ValueError("Invalid indoorPressure provided : " + str(indoorPressure) + ", skipping value");
        if self.prefix is not None:
            if self.prefix not in measure:
                measure[self.prefix] = {}
            measure = measure[self.prefix]
        measure["indoorTemp"] = indoorTemp
        measure["indoorPressure"] = indoorPressure
        tempSensorMessage = ", "
        if self.prefix is not None:
            tempSensorMessage += "[" + self.prefix + "]"
        tempSensorMessage += " temp=" + ("%2.2f'C" % indoorTemp) + ", pressure=" + ("%5.4f mbar" % indoorPressure)
        print(tempSensorMessage, end='')

    def shutdown(self):
        print("Shutdown " + self.getModuleName())

