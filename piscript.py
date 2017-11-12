import pimodule
import fetchfromes
import elasticsearch

def simpleHeater(esClient, measure, prefix):
    # print("Incoming measure : " + str(measure))
    # modeComfort = fetchfromes.extractFragment(measure, "heater.mode.comfort")
    # targetComfort = fetchfromes.extractFragment(measure, "heater.target.comfort")
    # targetStandby = fetchfromes.extractFragment(measure, "heater.target.standby")
    indoorTemp = fetchfromes.extractFragment(measure, "indoorTemp")
    index = "oswh-states"
    doc_type = "state"
    modeComfort = fetchfromes.llReadFromES(esClient, prefix + "." + "heater.mode.comfort", index, doc_type, esMode = "get")
    targetComfort = fetchfromes.llReadFromES(esClient, prefix + "." + "heater.target.comfort", index, doc_type, esMode = "get")
    targetStandby = fetchfromes.llReadFromES(esClient, prefix + "." + "heater.target.standby", index, doc_type, esMode = "get")
    print("Update : temp=" + str(indoorTemp) + ", mode=" + str(modeComfort) + ", targetComfort=" + str(targetComfort) + ", targetStandby=" + str(targetStandby))
    
    heaterCommand = "heaterOff"
    if modeComfort and indoorTemp < targetComfort:
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
    measure = {"pizero1":{"indoorTemp":15.27, "heater":{"mode":{"comfort": false},"target":{"comfort":18,"standby":14}}} }
    config = {"script":"pizero1Heater(measure)"}
    script = PiScript(config)
    script.update(measure)
    print("Measure : " + str(measure))
