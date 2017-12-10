'''
Utility class to monitor temperatures
'''

from piwatcher import pimodule
from piwatcher import bmp280

class TempWatcher(pimodule.PiModule):
    tempSensorBmp280 = None
    
    def __init__(self):
        pimodule.PiModule.__init__(self,"Temp")
        self.tempSensorBmp280 = bmp280.BMP280()
        chip_id, chip_version = self.tempSensorBmp280.read_id()

        if chip_id == 88:
	        self.tempSensorBmp280.reg_check()
        else:
            raise ValueError ("Unsupported chip : " + chip_id)        

    def update(self, measure):
        indoorTemp, indoorPressure = self.tempSensorBmp280.read()
        # Guard against absurd values
        if indoorPressure < 920.0:
            raise ValueError("Invalid indoorPressure provided : " + str(indoorPressure) + ", skipping value");
        measure["indoorTemp"] = indoorTemp
        measure["indoorPressure"] = indoorPressure
        tempSensorMessage = ", temp=" + ("%2.2f'C" % indoorTemp) + ", pressure=" + ("%5.4f mbar" % indoorPressure)
        print(tempSensorMessage, end='')

    def shutdown(self):
        print("Shutdown " + self.getModuleName())

