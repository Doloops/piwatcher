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
    busnum = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"Temp")
        if "address" in moduleConfig and moduleConfig["address"] == "0x76":
            self.address = 0x76
        if "prefix" in moduleConfig:
            self.prefix = moduleConfig["prefix"]
        if "model" in moduleConfig:
            self.model = moduleConfig["model"]
        if "busnum" in moduleConfig:
            self.busnum = moduleConfig["busnum"]
        self.initTempSensor()

    def initTempSensor(self):
        if self.model == "BMP280":
            self.tempSensor = bmp280.BMP280(address=self.address)
            chip_id, chip_version = self.tempSensor.read_id()

            if chip_id == 88:
                self.tempSensor.reg_check()
            else:
                raise ValueError ("Unsupported chip : " + str(chip_id) + ", " + str(chip_version))
            print("BMP280 OK")
        elif self.model == "BME280":
            self.tempSensor = bme280.BME280(address=self.address)
        else:
            raise ValueError ("Unsupported model : " + self.model)

    def update(self, measure):
        if self.tempSensor is None:
            self.initTempSensor()
        indoorTemp, indoorPressure = self.tempSensor.read()
        if self.model == "BME280":
            indoorHumidity = self.tempSensor.read_humidity()
        else:
            indoorHumidity = None

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
        if indoorHumidity is not None:
            measure["indoorHumidity"] = indoorHumidity
        tempSensorMessage = ", "
        if self.prefix is not None:
            tempSensorMessage += "[" + self.prefix + "]"
        tempSensorMessage += " temp=" + ("%2.2f'C" % indoorTemp) + ", pressure=" + ("%5.4f mbar" % indoorPressure)
        if indoorHumidity is not None:
            tempSensorMessage += " humidity=" + ("%3f %%" % indoorHumidity)
        print(tempSensorMessage, end='')

    def shutdown(self):
        print("Shutdown " + self.getModuleName())

