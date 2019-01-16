from piwatcher import pimodule
from piwatcher import fetchfromes
import redis
import json
import threading
import time

from datetime import datetime, timedelta

DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

class PiScript(pimodule.PiModule):
    verbose = False

    # States

    moduleConfig = None

    # Configuration

    states = {}
    subscribedUpdates = {}
    redisClient = None
    lastMeasure = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self, "PiScript")
        self.moduleConfig = moduleConfig
        if "wrapMeasureIn" in moduleConfig:
            self.wrapMeasureIn = moduleConfig["wrapMeasureIn"]

    def getRedisClient(self):
        if self.redisClient is not None:
            return self.redisClient
        if "hosts" in self.moduleConfig:
            redisHost = self.moduleConfig["hosts"][0]["host"]
            print("Connecting to redis host :" + redisHost)
            self.redisClient = redis.StrictRedis(host=redisHost, port=6379, db=0, decode_responses=True, 
                                                 socket_timeout=5, socket_connect_timeout=5)
        return self.redisClient

    def backgroundStateUpdate(self, key):
        pubsub = None
        while True:
            try:
                if pubsub is None:
                    pubsub = self.getRedisClient().pubsub()
                    pubsub.subscribe(key)
                message = pubsub.get_message(timeout=60)
                if message is not None and message["type"] == "message":
                    if self.verbose:
                        print ("data : " + message["data"] + " [" + str(type(message["data"]))+ "]")
                    stateValue = message["data"].strip('"')
                    stateValue = self.parseValue(stateValue)
                    if self.verbose:
                        print ("U{" + key + "=" + str(stateValue) + "}")
                    self.states[key] = stateValue
                    if self.lastMeasure is not None:
                        self.update(self.lastMeasure)
                        if "updateModule" in self.moduleConfig:
                            self.piwatcher.updateModule(self.moduleConfig["updateModule"], self.lastMeasure)
                        print(" => Updated")
            except Exception as e:
                print("Caught exception " + str(e))
                pubsub = None
                time.sleep(2)

    def getState(self, prefix, stateId, defaultValue = None, subscribe = True):
        if prefix is not None: 
            key = prefix + "." + stateId
        else:
            key = stateId
        if key in self.states:
            return self.states[key]
        if subscribe and key not in self.subscribedUpdates:
            print("Subscribing to key=" + str(key))
            thread = threading.Thread(target = self.backgroundStateUpdate, args=[key])
            self.subscribedUpdates[key] = thread
            thread.setDaemon(True)
            thread.start()
        value = self.getRedisClient().get(key)
        value = self.parseValue(value, defaultValue)
        self.states[key] = value
        return value

    def parseValue(self, value, defaultValue = None):
        if value is None:
            return defaultValue
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.lower() == "null":
            return None
        try:
            return float(value)
        except:
            return value
    
    def setState(self, prefix, stateId, stateValue):
        key = prefix + "." + stateId
        self.states[key] = stateValue
        if type(stateValue) is datetime:
            stateValueStr = stateValue.isoformat()
        elif type(stateValue) is str:
            stateValueStr = stateValue
        else:
            stateValueStr = json.dumps(stateValue)
        try:
            self.getRedisClient().set(key, stateValueStr)
            self.getRedisClient().publish(key, stateValueStr)
        except Exception as e:
            print("Caught exception while setting " + key + " : " + str(e) + " (value=" + str(stateValue) + ", type=" + str(type(stateValue)) + ")")
    
    def updateModeComfort(self, prefix):
        modeComfort = self.getState(prefix, "heater.mode.comfort")
        comfortStartTime = self.getState(prefix, "heater.comfort.startTime", subscribe=False)
        comfortTimeToLive = self.getState(prefix, "heater.comfort.ttl", 2)
        if self.verbose:
            print("Update : modeComfort=" + str(modeComfort) + ", comfortTimeToLive=" + str(comfortTimeToLive) 
                  + ", comfortStartTime=" + str(comfortStartTime))

        if modeComfort:
            if comfortStartTime is None:
                comfortStartTime = datetime.utcnow()
                self.setState(prefix, "heater.comfort.startTime", comfortStartTime)
            if isinstance(comfortStartTime, str):
                comfortStartTime = datetime.strptime(comfortStartTime, DATE_ISO_FORMAT)
            comfortEndTime = comfortStartTime + timedelta(hours=comfortTimeToLive)
            now = datetime.utcnow()
            if self.verbose:
                print("comfortStartTime=" + str(comfortStartTime) + ", now=" + str(now) + ", comfortEndTime=" + str(comfortEndTime))
            if now > comfortEndTime:
                print(", End of Comfort !", end='')
                modeComfort = False
                comfortStartTime = None
                self.setState(prefix, "heater.mode.comfort", modeComfort)
                self.setState(prefix, "heater.comfort.startTime", comfortStartTime)
                self.setState(prefix, "heater.comfort.remaingTime", 0)
            else:
                remainingTime = comfortEndTime - now
                self.setState(prefix, "heater.comfort.remaingTime", int(remainingTime.seconds / 60))
        else:
            if comfortStartTime is not None:
                self.setState(prefix, "heater.comfort.startTime", None)
                self.setState(prefix, "heater.comfort.remaingTime", 0)
        return modeComfort

    def getNormalTemp(self, prefix):
        if "hourlyTemps" in self.moduleConfig:
            hourlyTemps = self.moduleConfig["hourlyTemps"]
            hour = datetime.now().hour
            for period in hourlyTemps:
                if period["from"] <= hour and hour < period["to"]:
                    targetStandby = period["temp"]
                    self.setState(prefix, "heater.target.standby", targetStandby)
                    return targetStandby
        targetStandby = self.getState(prefix, "heater.target.standby")
        return targetStandby

    def simpleHeater(self, measure, prefix, indoorTempName = None):
        # print("Incoming measure : " + str(measure))
        if indoorTempName is not None:
            indoorTemp = self.getState(None, indoorTempName)
        else:
            indoorTemp = fetchfromes.extractFragment(measure, "indoorTemp")

        modeComfort = self.updateModeComfort(prefix)
        # We must evaluate normal temp now, to update UI with freshest timely values
        normalTemp = self.getNormalTemp(prefix)
        if modeComfort:
            targetTemp = self.getState(prefix, "heater.target.comfort")
        else:
            targetTemp = normalTemp

        if indoorTemp < targetTemp:
            heaterCommand = "heaterOn"
        else:
            heaterCommand = "heaterOff"
        self.setState(prefix, "heater.targetTemp", targetTemp)
        self.setState(prefix, "heater.command", heaterCommand)

        measurePrefix = ""
        if "prefix" in self.moduleConfig:
            measurePrefix = self.moduleConfig["prefix"] + "."
        fetchfromes.updateFragment(measure, measurePrefix + "heater.targetTemp", targetTemp)
        fetchfromes.updateFragment(measure, measurePrefix + "heater.command", heaterCommand)

    def getNormalState(self, prefix):
        if "hourlyState" in self.moduleConfig:
            hourlyState = self.moduleConfig["hourlyState"]
            hour = datetime.now().hour
            for period in hourlyState:
                if period["from"] <= hour and hour < period["to"]:
                    targetState = period["state"]
                    if targetState:
                        targetState = "relayOn"
                    else:
                        targetState = "relayOff"
#                    self.setState(prefix, "state", targetState)
                    return targetState
        return "relayOff"



    def simpleRelay(self, measure, prefix):
        targetState = self.getNormalState(prefix)
        print("simpleRelay prefix=" + prefix + " targetState=" + str(targetState) + ",", end='')
        self.setState(prefix, "state", targetState)
        measurePrefix = ""
        if "prefix" in self.moduleConfig:
            measurePrefix = str(self.moduleConfig["prefix"]) + "."
#        print("measurePrefix=" + measurePrefix)
        fetchfromes.updateFragment(measure, measurePrefix + "state", targetState)

    def commandRelay(self, measure, prefix):
        targetState = self.getState(prefix, "command")
        print("commandRelay prefix=" + prefix + " targetState=" + str(targetState) + ",", end='')
        if targetState:
            targetState = "relayOn"
        else:
            targetState = "relayOff"

        self.setState(prefix, "state", targetState)
        measurePrefix = ""
        if "prefix" in self.moduleConfig:
            measurePrefix = str(self.moduleConfig["prefix"]) + "."
#        print("measurePrefix=" + measurePrefix)
        fetchfromes.updateFragment(measure, measurePrefix + "state", targetState)


    def update(self, measure):
        self.lastMeasure = measure
        measure = self.mayWrap(measure)
        if self.verbose:
            print("Before SCRIPT : " + str(measure))
        eval(self.moduleConfig["script"])
        if self.verbose:
            print("After SCRIPT : " + str(measure))

if __name__ == "__main__":
    true = True
    false = False
    # measure = {"pizero1":{"indoorTemp":15.27, "heater":{"mode":{"comfort": false},"target":{"comfort":18,"standby":14}}} }
    measure = {"indoorTemp" : 14.87}
    config =  {"hosts":[{"host" : "osmc", "retry_on_timeout": true}],    
        "script":"simpleHeater(self.esClient, measure,'pizero1')"}
    script = PiScript(config)
    script.update(measure)
    print("Measure : " + str(measure))
