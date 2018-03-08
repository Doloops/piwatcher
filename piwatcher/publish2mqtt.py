from piwatcher import pimodule
from hbmqtt.client import MQTTClient

from datetime import datetime

import logging
import asyncio
import json

logger = logging.getLogger('piwatcher.publish2mqtt')

class Publish2MQTT(pimodule.PiModule):

    mqttClient = None
    topicRoot = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"Publish2MQTT")
        self.moduleConfig = moduleConfig
        self.topicRoot = moduleConfig["topicRoot"]

    @asyncio.coroutine
    def doUpdate(self, measure):
        mqttHost = self.moduleConfig["hosts"][0]
        if self.mqttClient is None:
            self.mqttClient = MQTTClient()
            yield from self.mqttClient.connect(mqttHost)
        yield from self.publishToMqtt(self.topicRoot, measure)
        logger.debug("messages published")

    @asyncio.coroutine
    def publishToMqtt(self, prefix="", body = None):
        if prefix != "" and not prefix.endswith("/"):
            prefix = prefix + "/"
        for key in body:
            logger.debug("At prefix=" + prefix + ", key=" + key + ", type=" + str(type(body[key])))
            if type(body[key]) is dict:
                yield from self.publishToMqtt(prefix + key, body[key])
            elif type(body[key]) is datetime:
                # Nothing to do here
                channel = None
            else:
                channel = prefix + key
                message = bytearray(json.dumps(body[key]), "utf-8")
                logger.debug("Publishing " + channel + "=" + str(message))
                yield from self.mqttClient.publish(channel, message, retain=True)

    def update(self, measure):
        logger.debug("Measure=" + json.dumps(measure))
        try:
            asyncio.get_event_loop().run_until_complete(self.doUpdate(measure))
        except:
            logger.exception("Publish failed !")
            # asyncio.get_event_loop().stop()

    def shutdown(self):
        print("Shutdown " + self.getModuleName())    
