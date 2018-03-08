from piwatcher import pimodule
from piwatcher import statescontroller
from hbmqtt.client import MQTTClient

from datetime import datetime

import logging
import asyncio
import json

logger = logging.getLogger('piwatcher.publish2mqtt')
logger.setLevel(logging.INFO)

class Publish2MQTT(pimodule.PiModule, statescontroller.StatesController):

    mqttClient = None
    topicRoot = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"Publish2MQTT")
        self.moduleConfig = moduleConfig
        self.topicRoot = moduleConfig["topicRoot"]

    def setPiWatcher(self, piwatcher):
        self.piwatcher = piwatcher
        piwatcher.setStatesController(self)

    async def getMQTTClient(self):
        if self.mqttClient is None:
            mqttHost = self.moduleConfig["hosts"][0]
            self.mqttClient = MQTTClient()
            await self.mqttClient.connect(mqttHost)
        return self.mqttClient
        
    async def doUpdate(self, measure):
        await self.publishFragment(self.topicRoot, measure)
        logger.debug("messages published")

    async def publishValue(self, channel, value):
        message = bytearray(json.dumps(value), "utf-8")
        logger.debug("Publishing " + channel + "=" + str(message))
        client = await self.getMQTTClient()
        await client.publish(channel, message, retain=True)

    async def publishFragment(self, prefix="", body = None):
        if prefix != "" and not prefix.endswith("/"):
            prefix = prefix + "/"
        for key in body:
            logger.debug("At prefix=" + prefix + ", key=" + key + ", type=" + str(type(body[key])))
            if type(body[key]) is dict:
                await self.publishFragment(prefix + key, body[key])
            elif type(body[key]) is datetime:
                # Nothing to do here
                channel = None
            else:
                channel = prefix + key
                await self.publishValue(channel, body[key])

    lastMeasure = None

    def update(self, measure):
        logger.debug("Measure=" + json.dumps(measure))
        try:
            asyncio.get_event_loop().run_until_complete(self.doUpdate(measure))
            self.lastMeasure = measure
        except:
            logger.exception("Publish failed !")
            # asyncio.get_event_loop().stop()

    def shutdown(self):
        print("Shutdown " + self.getModuleName())    

    subscribedChannels = {}

    subscribeChannelsTask = None

    async def asyncGetState(self, prefix, stateId, defaultValue, additionnalFuture):
        channel = (prefix + "." + stateId).replace(".", "/")
        updateFuture = asyncio.get_event_loop().create_future()
    
        if self.subscribeChannelsTask is None:
            self.subscribeChannelsTask = asyncio.get_event_loop().create_task(self.subscribeChannels())
                 
        if channel not in self.subscribedChannels:
            self.subscribedChannels[channel] = [updateFuture]
            if additionnalFuture is not None:
                self.subscribedChannels[channel].append(additionnalFuture)
            client = await self.getMQTTClient()
            logger.info("Subscribing to " + channel)
            await client.subscribe([(channel,0)])
        else:
            self.subscribedChannels[channel].append(updateFuture)

        await updateFuture
        logger.info("updateFuture done:" + str(updateFuture.done()))
        self.subscribedChannels[channel].remove(updateFuture)
        return updateFuture.result()

    async def subscribeChannels(self):
        client = await self.getMQTTClient()
        # for channel in self.subscribedChannels:
        #    logger.info("Subscribing to " + channel)
        #    await client.subscribe([(channel,0)])
        while True:
            message = await client.deliver_message()
            topic = message.publish_packet.variable_header.topic_name
            payload = json.loads(message.publish_packet.payload.data.decode("utf-8"))
            logger.info("Recieved topic=" + topic + ", payload=" + str(payload))
            if topic in self.subscribedChannels:
                futures = self.subscribedChannels[topic]
                for future in futures:
                    future.set_result(payload)

    class FakeFuture:
        def init(self):
            pass
        def set_result(self, value):
            logger.info("updateModule(self=" + repr(self) + ", value=" + repr(value) + ")")

    def getState(self, prefix, stateId, defaultValue = None, subscribe = True, subscribedModule = None):
        fakeFuture = self.FakeFuture()
        value = asyncio.get_event_loop().run_until_complete(self.asyncGetState(prefix, stateId, defaultValue, fakeFuture))
        return value

    def setState(self, prefix, stateId, stateValue):
        channel = (prefix + "." + stateId).replace(".", "/")
        asyncio.get_event_loop().run_until_complete(self.publishValue(channel, stateValue))

