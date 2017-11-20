import asyncio
import elasticsearch
import logging
import picadios.home
import picadios.controller
import picadios.ws.wsserver
import picadios.backends.esstate
import picadios.backends.redisstate
import redis

logger = logging.getLogger('websockets.server')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


# esClient = elasticsearch.Elasticsearch([{"host":"osmc"}, {"host":"pizero3"}, {"host":"192.168.1.63"}])
esClient = elasticsearch.Elasticsearch([{"host":"pizero3"}])

redisClient = redis.StrictRedis(host='pizero3', port=6379, db=0, decode_responses=True)
useRedis = True

sweetHome = picadios.home.Home() 
controller = picadios.controller.Controller(sweetHome)

for item in sweetHome.getItems():
    item = sweetHome.getItems()[item]
    stateId = item["id"]
    print("Configuring item " + stateId)
    if "es" in item:
        backend = picadios.backends.esstate.ESState(controller, item, esClient)
    elif useRedis:
        backend = picadios.backends.redisstate.RedisState(controller, item, redisClient)
    else:
        print("Ignoring item :" + stateId)
        continue
    print("Configured backend : " + str(backend))

print ("Preparing Webserver !")

wsserver = picadios.ws.wsserver.WSServer(sweetHome=sweetHome, controller=controller)
wsserver.startup()

print("Run forever !")
asyncio.get_event_loop().run_forever()

print ("Finished !")
