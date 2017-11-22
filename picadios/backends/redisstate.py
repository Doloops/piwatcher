from picadios.backends.basestate import BaseState
import json
import asyncio
import logging

logger = logging.getLogger("picadios.redisstate")

class RedisState(BaseState):

	stateId = None
	displayFormat = None
	defaultValue = None
	mapping = None
	itemType = None
	redisClient = None

	def __init__(self, controller, item, redisClient):
		BaseState.__init__(self, controller, item)
		self.redisClient = redisClient
		self.controller.registerBackendState(self)

	def parseRedisValue(self, stateValue):
		logger.debug("Redis Update : " + self.stateId + "=" + stateValue)
		if self.itemType == "float":
			stateValue = float(stateValue)
			if self.displayFormat is not None:
				stateValueStr = self.displayFormat % stateValue
			else:
				stateValueStr = json.dumps(stateValue)
		elif self.itemType == "bool":
			if self.mapping is not None and stateValue in self.mapping:
				stateValue = self.mapping[stateValue]
			else:
				stateValue = json.loads(stateValue)
			stateValueStr = json.dumps(stateValue)
		else:
			logger.error("Not supported ! " + self.itemType)
		return stateValue, stateValueStr

	def getState(self):
		stateValue = self.redisClient.get(self.stateId)
		if stateValue is not None:
			stateValue, stateValueStr = self.parseRedisValue(stateValue)
			logger.debug("Got value " + self.stateId + "=" + str(stateValue) + " (" + stateValueStr + ")")
		return stateValue

	async def asyncUpdate(self):
		stateValue = self.redisClient.get(self.stateId)
		if stateValue is not None:
			stateValue, stateValueStr = self.parseRedisValue(stateValue)
			logger.debug("Set initial value " + self.stateId + "=" + str(stateValue))
			await self.controller.notifyStateUpdate(self.stateId, stateValue, stateValueStr)
		elif self.defaultValue is not None:
			logger.info("Set default value " + self.stateId + "=" + str(self.defaultValue))
			await self.controller.notifyStateUpdate(self.stateId, self.defaultValue, json.dumps(self.defaultValue))
		
		pubsub = self.redisClient.pubsub()
		pubsub.subscribe(self.stateId)
		while True:
			message = pubsub.get_message()
			if message and message["type"] == "message":
				stateValue = message["data"].strip('"')
				stateValue, stateValueStr = self.parseRedisValue(stateValue)
				await self.controller.notifyStateUpdate(self.stateId, stateValue, stateValueStr)
			await asyncio.sleep(0.1)

	def modifyState(self, stateValue):
		logger.debug("Update Redis with " + self.getStateId() + "=" + json.dumps(stateValue))
		self.redisClient.set(self.getStateId(), json.dumps(stateValue))
		self.redisClient.publish(self.getStateId(), json.dumps(stateValue))
