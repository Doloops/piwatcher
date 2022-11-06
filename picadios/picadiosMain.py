import asyncio
import elasticsearch
import logging
import picadios.home
import picadios.controller
import picadios.ws.wsserver
import picadios.backends.esstate
import picadios.backends.redisstate
import asyncio_redis
import json
from os.path import expanduser

logging.basicConfig(format='%(asctime)s:%(name)s:%(funcName)s:%(levelname)s:%(message)s', level=logging.INFO)
logging.getLogger("elasticsearch").setLevel(logging.WARN)

logger = logging.getLogger('picadios.main')

logger.info("Welcome to Picadios Main !")

class PicadiosMain:
    def __init__(self):
        logger.info("Initing..")
        self.esClient = elasticsearch.Elasticsearch([{"host":"pizero3"}])
        
        # redisClient = redis.StrictRedis(host='pizero3', port=6379, db=0, decode_responses=True)
        # redisClient = asyncio_redis.Pool.create(host='pizero3', port=6379, poolsize=10)
        self.useRedis = True
        
        self.sweetHome = picadios.home.Home()
        
        self.controller = picadios.controller.Controller(self.sweetHome)
    
        with open(expanduser("~") + "/.picadios/ws.json") as wsConfig:
            wsConfig = json.loads(wsConfig.read())

        self.wsserver = picadios.ws.wsserver.WSServer(controller=self.controller, wsConfig = wsConfig)
        
    async def init(self):
        self.redisClient = await asyncio_redis.Pool.create(host='pi4b', port=6379, poolsize=100)
        for item in self.sweetHome.getItems():
            item = self.sweetHome.getItems()[item]
            stateId = item["id"]
            logger.debug("Configuring item " + stateId)
            if "es" in item:
                backend = picadios.backends.esstate.ESState(self.controller, item, self.esClient)
            elif self.useRedis:
                backend = picadios.backends.redisstate.RedisState(self.controller, item, self.redisClient)
                await backend.init()
            else:
                logger.warn("Ignoring item :" + stateId)
                continue
            logger.debug("Created backend=" + str(backend))
        
        logger.info("Preparing Webserver !")
        await self.wsserver.startup()
    
    async def start(self):
        await self.init()
        logger.info("Run forever !")
    
    async def runforever(self):
        try:
            asyncio.get_event_loop().run_forever()
        finally:
            logger.info("Finished !")
