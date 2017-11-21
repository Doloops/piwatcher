from piwatcher import pimodule
import elasticsearch
import time
import sys
import json
from datetime import datetime

class Push2ES(pimodule.PiModule):

    es = None
    hostname = None
    esIndex = None
    esType = None
    lastESUpdate = time.time()
    statsInterval = 60
    redisClient = None

    def __init__(self, hostname, moduleConfig, statsInterval=60):
        pimodule.PiModule.__init__(self,"Push2ES")
        self.es = elasticsearch.Elasticsearch(moduleConfig["hosts"] )
        self.hostname = hostname
        self.esIndex = moduleConfig["index"]
        self.esType = moduleConfig["type"]
        self.statsInterval = statsInterval
        
        if "redis" in moduleConfig:
            import redis
            self.redisClient = redis.StrictRedis(host=moduleConfig["redis"]["host"], port=6379, db=0, decode_responses=True)

    def publishToRedis(self, prefix="", body = None):
        if prefix != "" and not prefix.endswith("."):
            prefix = prefix + "."
        for key in body:
            # print ("At prefix=" + prefix + ", key=" + key + ", type=" + str(type(body[key])))
            if type(body[key]) is dict:
                self.publishToRedis(prefix + key, body[key])
            elif type(body[key]) is datetime:
                # Nothing to do here
                channel = None
            else:
                channel = prefix + key
                # print("Publish " + channel + " = " + str(body[key]))
                try:
                    self.redisClient.set(channel, json.dumps(body[key]))
                    self.redisClient.publish(channel, json.dumps(body[key]))
                except:
                    print("Could not push to Redis: ", sys.exc_info()[0])    

    def update(self, measure):
        esbody = {"timestamp": datetime.utcnow()}
        esbody[self.hostname] = measure
        
        if self.redisClient is not None:
            self.publishToRedis(body = esbody)
    
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
        

