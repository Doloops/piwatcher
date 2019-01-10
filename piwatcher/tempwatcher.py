'''
Utility class to monitor temperatures
'''

from piwatcher import pimodule
from piwatcher import bmp280
from piwatcher import bme280

class TempWatcher(pimodule.PiModule):
    tempSensor = None
    prefix = None
    address = 0x77
    model = "BMP280"
    
    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"Temp")
        if "address" in moduleConfig and moduleConfig["address"] == "0x76":
            self.address = 0x76
        if "prefix" in moduleConfig:
            self.prefix = moduleConfig["prefix"]
        if "model" in moduleConfig:
            self.prefix = moduleConfig["model"]
        self.initTempSensor()
            
    def initTempSensor(self):
        if self.model == "BMP280":
            self.tempSensor = bmp280.BMP280(address=self.address)
            chip_id, chip_version = self.tempSensor.read_id()

            if chip_id == 88:
                self.tempSensor.reg_check()
            else:
                raise ValueError ("Unsupported chip : " + chip_id + ", " + chip_version)
         elif self.model == "BME280":
            self.tempSensor = bme280.BME280(address=self.address)
         else
            raise ValueError ("Unsupported model : " + self.model)

    def update(self, measure):
        if self.tempSensor is None:
            self.initTempSensor()
        indoorTemp, indoorPressure = self.tempSensor.read()
        # Guard against absurd values
        if indoorPressure < 920.0:
            print ("Invalid indoorPressure provided : " + str(indoorPressure) + ", skipping value");
            self.tempSensor.bus.close()
            self.tempSensor = None
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

