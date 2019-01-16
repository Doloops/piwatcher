from piwatcher import piwatcherconfig
from piwatcher import pimodule
import time
import sys
import RPi.GPIO as GPIO
from piwatcher import fetchfromes
from datetime import datetime

class PiCommandWatcher(pimodule.PiModule):
    channels = None
    commands = None
    propertyName = None
    defaultValue = None
    pwms = {}

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"PiCommandWatcher")
        GPIO.setmode(GPIO.BOARD)
        self.channels = moduleConfig["channels"]
        self.commands = moduleConfig["commands"]
        self.propertyName = moduleConfig["property"]
        if "defaultValue" in moduleConfig:
            self.defaultValue = moduleConfig["defaultValue"]
        if "wrapMeasureIn" in moduleConfig:
            self.wrapMeasureIn = moduleConfig["wrapMeasureIn"]
        for name in self.channels:
            channel = self.channels[name]
            if "pinout" in channel:
                pinout = channel["pinout"]
                print("Configuring channel " + name + " to pinout " + str(pinout))
                GPIO.setup(pinout, GPIO.OUT)
                GPIO.output(pinout, False)
            else:
                raise ValueError("Invalid channel " + name + " : " + str(channel))
        if "init" in self.commands:
            self.applyCommand("__init__", "init")

    def update(self, measure):
        measure = self.mayWrap(measure)
        value = fetchfromes.extractFragment(measure, self.propertyName)
        if value is None and self.defaultValue is not None:
            value = self.defaultValue
            print (", update default " + self.propertyName + "=" + str(value), end='')
        if value is not None:
            print(", update " + self.propertyName + "=" + str(value), end='')
            self.applyCommand(self.propertyName, value)

    def __update(self, measure):
        timestamp = datetime.utcnow()
        try:
            result = self.es.get(index = self.esIndex, doc_type = self.esType, id = self.esId)
            if result["found"] == True:
                firstResult = result["_source"]
                print(", " + self.esPropertyName, end='')
                if self.esPropertyName not in firstResult:
                    raise ValueError("No property " + self.esPropertyName + " in result " + str(firstResult))
                value = firstResult[self.esPropertyName]
                print("=" + str(value), end='')

                measure[self.esType] = {}
                measure[self.esType][self.esPropertyName] = value
                self.applyCommand(self.esPropertyName, value)
            else:
                raise ValueError("Wrong number of results " + str(result))
        except Exception as err:
            print("[Default=" + self.esPropertyDefaultValue + "]", end='')
            self.applyCommand(self.esPropertyName, self.esPropertyDefaultValue)
            raise err

    def applyCommandKey(self, commandKey, commandValue):
#        print("k:" + commandKey + "=" + str(commandValue))
        if commandKey == "sleep":
            time.sleep(commandValue)
        elif commandKey == "command":
            self.applyCommand(commandKey, commandValue)
        elif commandKey in self.channels:
            channel = self.channels[commandKey]
            if "pinout" in channel:
                pinout = channel["pinout"]
                if isinstance(commandValue, bool):
                    if commandKey in self.pwms:
#                        print("Disabling PWM for channel :" + commandKey)
                        self.pwms[commandKey].stop()
                        self.pwms.pop(commandKey)
                        # When disabling PWM, we have to wait a bit before setting value
                        freq = channel["freq"]
                        time.sleep(2/freq)
                    GPIO.output(pinout, commandValue)
                else:
                    if commandKey not in self.pwms:
                        freq = channel["freq"]
                        pwm = GPIO.PWM(pinout, freq)
                        pwm.start(0)
                        self.pwms[commandKey] = pwm
#                        print("Setting PWM for channel :" + commandKey)
                    else:
                        pwm = self.pwms[commandKey]
                    pwm.ChangeDutyCycle(commandValue)
        else:
            raise ValueError("Invalid command key " + commandKey)

    def applyCommand(self, propertyName, propertyValue):
        if propertyValue in self.commands:
            command = self.commands[propertyValue]
            if type(command) is list:
                for commandEntry in command:
                    for commandKey in commandEntry:
                        commandValue = commandEntry[commandKey]
                        self.applyCommandKey(commandKey, commandValue)
            elif type(command) is dict:
                for commandKey in command:
                    commandValue = command[commandKey]
                    self.applyCommandKey(commandKey, commandValue)
            else:
                raise ValueError("Invalid type for command " + propertyValue)
        else:
            raise ValueError("Unknown value '" + propertyValue + "' for property " + propertyName + ", commands=" + str(self.commands.keys()))

    def shutdown(self):
        print("Shutdown " + self.getModuleName())
        for name in self.channels:
            channel = self.channels[name]
            if name in self.pwms:
                pinout = channel["pinout"]
                print("Disabling PWM channel " + name + ", pwm " + str(pinout))
                self.pwms[name].stop();
            if "pinout" in channel:
                pinout = channel["pinout"]
                print("Disabling channel " + name + ", pinout " + str(pinout))
                GPIO.output(pinout, False)
        GPIO.cleanup()


if __name__=="__main__":
    pwConfig = piwatcherconfig.PiWatcherConfig.getConfig()
    if "picommander" in pwConfig:    
        picmd = PiCommandWatcher(moduleConfig = pwConfig["picommander"])
    try:
        while True:
            print("Select command:")
            input = sys.stdin.readline().strip()
            print("Read : " + input)
            try:
                picmd.applyCommand("input", input)
            except Exception as err:
                print(" ! Caught " + str(err))
                print("Invalid input : " + input)
    finally:
        picmd.shutdown()
        
# Garbage

# Sample ES query from Python
#        query = {"query":
#            {"bool":
#                {"must":[
#                    {"range":{"timestamp":{"lt":timestamp}}}
#                    ],
#                 "must_not":[],"should":[]}},
#             "from":0,"size":1,
#             "sort":[{"timestamp":{"order":"desc"}}],
#             "aggs":{}}

