import pimodule
import elasticsearch
import time
from datetime import datetime

class Push2ES(pimodule.PiModule):

    es = None
    hostname = None
    esIndex = None
    esType = None
    lastESUpdate = time.time()
    statsInterval = 60

    def __init__(self, hosts, hostname, esIndex, esType, statsInterval):
        pimodule.PiModule.__init__(self,"Push2ES")
        self.es = elasticsearch.Elasticsearch(hosts)
        self.hostname = hostname
        self.esIndex = esIndex
        self.esType = esType
        self.statsInterval = statsInterval
        
    def update(self, measure):
        esbody = {"timestamp": datetime.utcnow()}
        esbody[self.hostname] = measure
    
        tnow = time.strftime("%Y%m%d-%H%M%S")
        now = time.time()
        if ( now - self.lastESUpdate >= self.statsInterval ):
            try:
                tsBefore = time.time()
                self.es.index(index=self.esIndex, doc_type=self.esType, id=tnow, body=esbody)
                print (" * Indexed in " + ("%.3f s" % (time.time() - tsBefore)), end='')
                self.lastESUpdate = now
            except:
                print("Could not index to ES: ", sys.exc_info()[0])    
    
    def shutdown(self):
        print("Shutdown " + self.getModuleName())    
        

