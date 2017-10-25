import piwatcherconfig
import pimodule
import elasticsearch
import time
import sys
import RPi.GPIO as GPIO
from datetime import datetime

class PiCommandWatcher(pimodule.PiModule):
    es = None
    hostname = None
    esIndex = None
    esType = None
    esId = None
    esPropertyName = None
    esPropertyDefaultValue = None
    channels = None
    commands = None
    lastESUpdate = time.time()
    statsInterval = 60
    pwms = {}

    def __init__(self, hosts, hostname, esIndex, esType, esId, esPropertyName, esPropertyDefaultValue, channels, commands):
        pimodule.PiModule.__init__(self,"PiCommandWatcher")
        GPIO.setmode(GPIO.BOARD)
        self.es = elasticsearch.Elasticsearch(hosts)
        self.hostname = hostname
        self.esIndex = esIndex
        self.esType = esType
        self.esId = esId
        self.esPropertyName = esPropertyName
        self.esPropertyDefaultValue = esPropertyDefaultValue;
        print("esPropertyName=" + self.esPropertyName)
        self.channels = channels
        self.commands = commands
        for name in self.channels:
            channel = self.channels[name]
            if "pinout" in channel:
                pinout = channel["pinout"]
                print("Configuring channel " + name + " to pinout " + str(pinout))
                GPIO.setup(pinout, GPIO.OUT)
                GPIO.output(pinout, False)
#            elif "pwm" in channel:
#                pinout = channel["pwm"]
#                freq = channel["freq"]
#                print("Configuring channel " + name + " to pwm " + str(pinout) + ", freq=" + str(freq))
#                GPIO.setup(pinout, GPIO.OUT)
#                pwm = GPIO.PWM(pinout, freq)
#                pwm.start(0)
#                self.pwms[name] = pwm

    def update(self, measure):
        timestamp = datetime.utcnow()
        query = {"query":
            {"bool":
                {"must":[
                    {"range":{"timestamp":{"lt":timestamp}}}
                    ],
                 "must_not":[],"should":[]}},
             "from":0,"size":1,
             "sort":[{"timestamp":{"order":"desc"}}],
             "aggs":{}}
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
        print("k:" + commandKey + "=" + str(commandValue))
        if commandKey == "sleep":
            time.sleep(commandValue)
        elif commandKey in self.channels:
            channel = self.channels[commandKey]
            if "pinout" in channel:
                pinout = channel["pinout"]
                if isinstance(commandValue, bool):
                    if commandKey in self.pwms:
                        print("Disabling PWM for channel :" + commandKey)
                        self.pwms[commandKey].stop()
                        self.pwms.pop(commandKey)
                    GPIO.output(pinout, commandValue)
                else:
                    if commandKey not in self.pwms:
                        freq = channel["freq"]
                        pwm = GPIO.PWM(pinout, freq)
                        pwm.start(0)
                        self.pwms[commandKey] = pwm
                        print("Setting PWM for channel :" + commandKey)
                    else:
                        pwm = self.pwms[commandKey]
                        
                    pwm.ChangeDutyCycle(commandValue)
#                GPIO.output(pinout, commandValue)
#            elif "pwm" in channel:
#                if isinstance(commandValue, bool):
#                    if commandValue:
#                        commandValue = 50
#                    else:
#                        commandValue = 0
#                self.pwms[commandKey].ChangeDutyCycle(commandValue)
#                pinout = channel["pwm"]
#                print("{channel:" + commandKey + ", pin:" + str(pinout) + "=" + str(commandValue) + "}")
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
        picmd = PiCommandWatcher(
            hosts = pwConfig["picommander"]["hosts"], 
            hostname = pwConfig["hostname"],
            esIndex = pwConfig["picommander"]["index"], 
            esType = pwConfig["picommander"]["type"],
            esId = pwConfig["picommander"]["id"],
            esPropertyName = pwConfig["picommander"]["property"],
            esPropertyDefaultValue = pwConfig["picommander"]["defaultValue"],        
            channels = pwConfig["picommander"]["channels"],
            commands = pwConfig["picommander"]["commands"]
            )
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
