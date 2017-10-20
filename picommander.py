import piwatcherconfig
import sys
import elasticsearch
import time
from datetime import datetime

print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))

class PiCommander:
    es = None
    def __init__(self, hosts):
        self.es = elasticsearch.Elasticsearch(hosts)

    def push(self, esIndex, esType, esPropertyName, esPropertyValue):
        esbody = {"timestamp": datetime.utcnow()}
        esbody[esPropertyName] = esPropertyValue
        tnow = time.strftime("%Y%m%d-%H%M%S")
        self.es.index(index=esIndex, doc_type=esType, id=tnow, body=esbody)

pwConfig = piwatcherconfig.PiWatcherConfig.getConfig()
hosts = pwConfig["elastic"]["hosts"]

commander = PiCommander(hosts)

esIndex = sys.argv[1]
esType = sys.argv[2]
esPropertyName = sys.argv[3]
esPropertyValue = sys.argv[4]

print("Pushing index=" + esIndex + ", type=" + esType + " : " + esPropertyName + "=" + esPropertyValue)

commander.push(esIndex, esType, esPropertyName, esPropertyValue)

