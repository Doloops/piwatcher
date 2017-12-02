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
	useBackgroundThread = False

	def __init__(self, controller, item, redisClient):
		BaseState.__init__(self, controller, item)
		self.redisClient = redisClient
		self.controller.registerBackendState(self)
		# Now initialize value
		stateValue = self.redisClient.get(self.stateId)
		if stateValue is None and self.defaultValue is not None:
			logger.info("Setting default value " + self.stateId + "=" + str(self.defaultValue))
			self.modifyState(self.defaultValue)
		if self.useBackgroundThread:
			pubsub = self.redisClient.pubsub()
			pubsub.subscribe(**{self.stateId: self.messageHandler} )
			pubsub.run_in_thread(sleep_time = 1, daemon = True)
	
	def messageHandler(self, message):
		logger.debug("Got message " + str(message))
		if message and message["type"] == "message":
			stateValue = message["data"].strip('"')
			logger.debug("asyncUpdate() " + self.stateId + "=" + stateValue)
			stateValue, stateValueStr = self.parseRedisValue(stateValue)
			self.controller.notifyStateUpdate(self.stateId, stateValue, stateValueStr)		

	def parseRedisValue(self, stateValue):
		logger.debug("parseRedisValue() RAW : " + self.stateId + "=" + stateValue)
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
		logger.debug("parseRedisValue() " + self.stateId + "=" + str(stateValue) + ", str=" + stateValueStr)
		return stateValue, stateValueStr

	def getState(self):
		stateValue = self.redisClient.get(self.stateId)
		if stateValue is not None:
			stateValue = stateValue.strip('"')
			logger.debug("getState() RAW : " + self.stateId + "=" + stateValue)
			stateValue, stateValueStr = self.parseRedisValue(stateValue)
			logger.debug("getState() : Got value " + self.stateId + "=" + str(stateValue) + " str=" + stateValueStr)
		return stateValue

	async def asyncUpdate(self):
		if self.useBackgroundThread:
			return
		pubsub = None
		while True:
			try:
				if pubsub is None:
					pubsub = self.redisClient.pubsub()
					pubsub.subscribe(self.stateId)
				message = pubsub.get_message()
				# logger.debug("For " + self.stateId + ", received message :" + str(message))
				if message and message["type"] == "message":
					stateValue = message["data"].strip('"')
					logger.debug("asyncUpdate() " + self.stateId + "=" + stateValue)
					stateValue, stateValueStr = self.parseRedisValue(stateValue)
					await self.controller.notifyStateUpdate(self.stateId, stateValue, stateValueStr)
				await asyncio.sleep(1)
			except Exception as e:
				logger.error("Caught exception " + str(e))
				pubsub = None
				await asyncio.sleep(1)

	def modifyState(self, stateValue):
		logger.debug("Update Redis with " + self.getStateId() + "=" + json.dumps(stateValue))
		self.redisClient.set(self.getStateId(), json.dumps(stateValue))
		self.redisClient.publish(self.getStateId(), json.dumps(stateValue))
