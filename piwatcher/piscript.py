from piwatcher import pimodule
from piwatcher import fetchfromes
import redis
import json
import threading

from datetime import datetime, timedelta

DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

class PiScript(pimodule.PiModule):
    
    verbose = False
    states = {}
    subscribedUpdates = {}
    
    def backgroundStateUpdate(self, key):
        pubsub = self.redisClient.pubsub()
        pubsub.subscribe(key)
        for message in pubsub.listen():
            if message["type"] == "message":
                if self.verbose:
                    print ("data : " + message["data"] + " [" + str(type(message["data"]))+ "]")
                stateValue = message["data"].strip('"')
                stateValue = self.parseValue(stateValue)
                if True:
                    print ("U{" + key + "=" + str(stateValue) + "}")
                self.states[key] = stateValue
                if self.lastMeasure is not None:
                    self.update(self.lastMeasure)
                    self.piwatcher.updateModule("PiCommandWatcher", self.lastMeasure)

    def getState(self, prefix, stateId, defaultValue = None, subscribe = True):
        key = prefix + "." + stateId
        if key in self.states:
            return self.states[key]
        if subscribe and key not in self.subscribedUpdates:
            thread = threading.Thread(target = self.backgroundStateUpdate, args=[key])
            self.subscribedUpdates[key] = thread
            thread.setDaemon(True)
            thread.start()
        value = self.redisClient.get(key)
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
        else:
            stateValueStr = json.dumps(stateValue)
        self.redisClient.set(key, stateValueStr)
        self.redisClient.publish(key, stateValueStr)
    
    def simpleHeater(self, measure, prefix):
        # print("Incoming measure : " + str(measure))
        indoorTemp = fetchfromes.extractFragment(measure, "indoorTemp")
        modeComfort = self.getState(prefix, "heater.mode.comfort")
        targetComfort = self.getState(prefix, "heater.target.comfort")
        targetStandby = self.getState(prefix, "heater.target.standby")
        comfortTimeToLive = self.getState(prefix, "heater.comfort.ttl", 2)
        comfortStartTime = self.getState(prefix, "heater.comfort.startTime", subscribe=False)
        if self.verbose:
            print("Update : temp=" + str(indoorTemp) + ", modeComfort=" + str(modeComfort) + ", targetComfort=" + str(targetComfort)
                   + ", targetStandby=" + str(targetStandby) + ", comfortTimeToLive=" + str(comfortTimeToLive) + ", comfortStartTime=" + str(comfortStartTime))
    
        heaterCommand = "heaterOff"
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
    
        if modeComfort:
            if indoorTemp < targetComfort:
                heaterCommand = "heaterOn"
        elif indoorTemp < targetStandby:
                heaterCommand = "heaterOn"
        self.setState(prefix, "heater.command", heaterCommand)
        # print("=> heaterCommand=" + heaterCommand)
        fetchfromes.updateFragment(measure, "heater.command", heaterCommand)

    script = None
    redisClient = None
    lastMeasure = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self, "PiScript")
        self.script = moduleConfig["script"]
        if "wrapMeasureIn" in moduleConfig:
            self.wrapMeasureIn = moduleConfig["wrapMeasureIn"]
        if "hosts" in moduleConfig:
            self.redisClient = redis.StrictRedis(host=moduleConfig["hosts"][0]["host"], port=6379, db=0, decode_responses=True)
            # self.esClient = elasticsearch.Elasticsearch(moduleConfig["hosts"])

    def update(self, measure):
        self.lastMeasure = measure
        measure = self.mayWrap(measure)
        if self.verbose:
            print("Before SCRIPT : " + str(measure))
        eval(self.script)
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
