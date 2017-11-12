import pimodule
import fetchfromes
import elasticsearch
from datetime import datetime, timedelta

DATE_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

def getState(esClient, prefix, stateId, defaultValue = None):
    index = "oswh-states"
    doc_type = "state"
    return fetchfromes.llReadFromES(esClient, prefix + "." + stateId, index, doc_type, esMode = "get", defaultValue=defaultValue)

def setState(esClient, prefix, stateId, stateValue):
    index = "oswh-states"
    doc_type = "state"
    fetchfromes.llWriteStateToES(esClient, prefix + "." + stateId, index, doc_type, stateValue = stateValue)

def simpleHeater(esClient, measure, prefix):
    # print("Incoming measure : " + str(measure))
    indoorTemp = fetchfromes.extractFragment(measure, "indoorTemp")
    modeComfort = getState(esClient, prefix, "heater.mode.comfort")
    targetComfort = getState(esClient, prefix, "heater.target.comfort")
    targetStandby = getState(esClient, prefix, "heater.target.standby")
    comfortTimeToLive = getState(esClient, prefix, "heater.comfort.ttl", 240)
    comfortStartTime = getState(esClient, prefix, "heater.comfort.startTime")
    if False:
        print("Update : temp=" + str(indoorTemp) + ", modeComfort=" + str(modeComfort) + ", targetComfort=" + str(targetComfort)
               + ", targetStandby=" + str(targetStandby) + ", comfortTimeToLive=" + str(comfortTimeToLive) + ", comfortStartTime=" + str(comfortStartTime))

    heaterCommand = "heaterOff"
    if modeComfort:
        if comfortStartTime is None:
            comfortStartTime = datetime.utcnow()
            # fetchfromes.llWriteStateToES(esClient, prefix + "." + "heater.comfort.startTime", "oswh-states", "state", stateValue = comfortStartTime)
            setState(esClient, prefix, "heater.comfort.startTime", comfortStartTime)
        if isinstance(comfortStartTime, str):
            comfortStartTime = datetime.strptime(comfortStartTime, DATE_ISO_FORMAT)
        comfortEndTime = comfortStartTime + timedelta(hours=comfortTimeToLive)
        now = datetime.utcnow()
        # print("comfortStartTime=" + str(comfortStartTime) + ", now=" + str(now) + ", comfortEndTime=" + str(comfortEndTime))
        if now > comfortEndTime:
            print(", End of Comfort !", end='')
            modeComfort = False
            comfortStartTime = None
            setState(esClient, prefix, "heater.mode.comfort", modeComfort)
            setState(esClient, prefix, "heater.comfort.startTime", comfortStartTime)
            setState(esClient, prefix, "heater.comfort.remaingTime", 0)
        else:
            remainingTime = comfortEndTime - now
            setState(esClient, prefix, "heater.comfort.remaingTime", int(remainingTime.seconds / 60))

    if modeComfort:
        if indoorTemp < targetComfort:
            heaterCommand = "heaterOn"
    elif indoorTemp < targetStandby:
        heaterCommand = "heaterOn"
    # print("=> heaterCommand=" + heaterCommand)
    fetchfromes.updateFragment(measure, "heater.command", heaterCommand)

class PiScript(pimodule.PiModule):
    script = None
    
    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self, "PiScript")
        self.script = moduleConfig["script"]
        if "wrapMeasureIn" in moduleConfig:
            self.wrapMeasureIn = moduleConfig["wrapMeasureIn"]
        if "hosts" in moduleConfig:
            self.esClient = elasticsearch.Elasticsearch(moduleConfig["hosts"])
        
    def update(self, measure):
        measure = self.mayWrap(measure)
        # print("Before SCRIPT : " + str(measure))
        eval(self.script)
        # print("After SCRIPT : " + str(measure))
        
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
