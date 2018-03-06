from piwatcher import pimodule
import RPi.GPIO as GPIO

class PiDigitalSensor(pimodule.PiModule):
    
    moduleConfig = None
    digitalPin = None
    mapping = None
    
    GPIO.setmode(GPIO.BOARD)
    
    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"PiDigitalSensor")
        self.moduleConfig = moduleConfig
        self.digitalPin = moduleConfig["digitalPin"]
        GPIO.setup(self.digitalPin, GPIO.IN)
        self.mapping = moduleConfig["mapping"]
        self.propertyName = moduleConfig["propertyName"] 
        
    def update(self, measure):
        state = GPIO.input(self.digitalPin)
        stateValue = self.mapping[state]
        measure[self.propertyName] = stateValue
        print(", (st=" + str(state) + ") " + self.propertyName + "=" + stateValue, end='')
        
    def shutdown(self):
        print("Shutdown " + self.getModuleName())        
