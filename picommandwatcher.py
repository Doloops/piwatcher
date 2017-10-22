import pimodule
import elasticsearch
import time
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
            pinout = channel["pinout"]
            print("Configuring channel " + name + " to pinout " + str(pinout))
            GPIO.setup(pinout, GPIO.OUT)

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

    def applyCommand(self, propertyName, propertyValue):
        if propertyValue in self.commands:
            command = self.commands[propertyValue]
            for commandKey in command:
                commandValue = command[commandKey]
                if commandKey in self.channels:
                    channel = self.channels[commandKey]
                    pinout = channel["pinout"]
#                    print(", {channel:" + commandKey + ", pin:" + str(pinout) + "=" + str(commandValue) + "}", end='')
                    GPIO.output(pinout, commandValue)
                else:
                    raise ValueError("Invalid command key " + commandKey)
        else:
            raise ValueError("Unknown value " + propertyValue + " for property " + propertyName)

    def shutdown(self):
        print("Shutdown " + self.getModuleName())    
        GPIO.cleanup()

