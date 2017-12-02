import asyncio
import elasticsearch
import logging
import picadios.home
import picadios.controller
import picadios.ws.wsserver
import picadios.backends.esstate
import picadios.backends.redisstate
import redis

logging.basicConfig(format='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s', level=logging.DEBUG)
logging.getLogger("elasticsearch").setLevel(logging.WARN)

logger = logging.getLogger('picadios.main')

logger.info("Welcome to Picadios Main !")

class PicadiosMain:
    def __init__(self):
        logger.info("Initing..")
        esClient = elasticsearch.Elasticsearch([{"host":"pizero3"}])
        
        redisClient = redis.StrictRedis(host='pizero3', port=6379, db=0, decode_responses=True)
        useRedis = True
        
        sweetHome = picadios.home.Home() 
        controller = picadios.controller.Controller(sweetHome)
        
        for item in sweetHome.getItems():
            item = sweetHome.getItems()[item]
            stateId = item["id"]
            logger.debug("Configuring item " + stateId)
            if "es" in item:
                backend = picadios.backends.esstate.ESState(controller, item, esClient)
            elif useRedis:
                backend = picadios.backends.redisstate.RedisState(controller, item, redisClient)
            else:
                logger.warn("Ignoring item :" + stateId)
                continue
            logger.debug("Created backend=" + str(backend))
        
        logger.info("Preparing Webserver !")
        
        wsserver = picadios.ws.wsserver.WSServer(controller=controller)
        wsserver.startup()
    
    def start(self):
        logger.info("Run forever !")
        try:
            asyncio.get_event_loop().run_forever()
        finally:
            logger.info("Finished !")
