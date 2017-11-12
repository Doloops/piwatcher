import pimodule
import elasticsearch
import time
import sys
from datetime import datetime

def updateFragment(fragmentRoot, stateId, stateValue):
    idParts = stateId.split('.')
    fragment = fragmentRoot
    for part in idParts[0:len(idParts) - 1]:
        if part not in fragment:
            fragment[part] = {}
        fragment = fragment[part]
    fragment[idParts[len(idParts)-1]] = stateValue

# Low-level save to ES
def llWriteStateToES(esClient, stateId, index, doc_type, esMode = "get", stateValue = None):
    if esMode != "get":
        print ("Invalid esMode = " + esMode + " for stateId=" + stateId)
        return
    print ("Writing state " + stateId + "=" + str(stateValue))
    fragmentRoot = {}
    updateFragment(fragmentRoot, stateId, stateValue)
    print ("Writing state " + stateId + " fragment : " + str(fragmentRoot))
    esClient.index(index=index, doc_type=doc_type, id=stateId, body=fragmentRoot)

# Low-level fetch from ES
def llReadFromES(esClient, stateId, index, doc_type, esMode = None, defaultValue = None):
    print("Searching " + stateId + " in index=" + index + ", doc_type=" + doc_type + ", esMode=" + esMode)
    if esMode == "search":
        query = {"query": {"bool": {"must": {"match_all":{}}}}, "sort":[{"timestamp":{"order":"desc"}}]}
        esResult = esClient.search(index=index, doc_type=doc_type, body = query)
#        print("esResult=" + str(esResult))
        if esResult["hits"]["total"] < 1:
            print("No result !")
            return None
        esResult = esResult["hits"]["hits"][0]["_source"]
    elif esMode == "get":
        try:
            esResult = esClient.get(index=index, doc_type=doc_type, id = stateId)
        except elasticsearch.NotFoundError as e:
            print ("Not found ! " + str(e))
            esResult = None
        if esResult is not None and esResult["found"] == True:
            esResult = esResult["_source"]
        else:
            print ("No result found for " + stateId)
            esResult = None

        if esResult is None and defaultValue is not None:
            llWriteStateToES(esClient = esClient, stateId = stateId, index = index, doc_type = doc_type, esMode = esMode, stateValue = defaultValue)
    else:
        print ("ES Mode " + esMode + " invalid for stateId=" + stateId)
        return None

    if esResult is not None:
        # stateValue = esResult[hostName][valueName]
        fragment = esResult
        idParts = stateId.split('.')
        for part in idParts:
            if part not in fragment:
                print ("ERROR ! No component " + part + " in " + str(fragment))
                return
            fragment = fragment[part]
        stateValue = fragment
        return stateValue
    return None

class FetchFromES(pimodule.PiModule):

    es = None
    hostname = None
    esIndex = None
    esDocType = None
    esStateIds = None
    
    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"FetchFromES")
        self.es = elasticsearch.Elasticsearch(moduleConfig["hosts"])
#        self.hostname = moduleConfig["hostName"]
        self.esIndex = moduleConfig["index"]
        self.esDocType = moduleConfig["doc_type"]
        self.esStateIds = moduleConfig["states"]
#        self.statsInterval = statsInterval
        
    def update(self, measure):
        for stateId in self.esStateIds:
            stateValue = llReadFromES(self.es, stateId, self.esIndex, self.esDocType, "get", None)
            print ("Got stateId=" + stateId + " => " + str(stateValue))
            updateFragment(measure, stateId, stateValue)
        
if __name__=="__main__":
    # pwConfig = piwatcherconfig.PiWatcherConfig.getConfig()
    true = True
    fetchFromEsConfig = {
        "hosts":[{"host" : "osmc", "retry_on_timeout": true}],
         "index":"oswh-states", "doc_type":"state",
         "states":["pizero1.heater.target.comfort","pizero1.heater.mode.comfort"]
        }
    fetch = FetchFromES(fetchFromEsConfig)
    measure = {}
    fetch.update(measure)
    print ("Updated : " + str(measure))
