from picadios.backends.basestate import BaseState
import fetchfromes
import json
import asyncio

class ESState(BaseState):

	esClient = None
	esMode = "search"
	esIndex = None
	esDocType = None
	interval = 30

	def __init__(self, controller, item, esClient):
		BaseState.__init__(self, controller, item)
		self.esClient = esClient
		if "es_mode" in item["es"]:
			self.esMode = item["es"]["es_mode"]
		self.esIndex = item["es"]["index"]
		self.esDocType = item["es"]["doc_type"]
		self.controller.registerBackendState(self)

	async def asyncUpdate(self):
		# esClient, stateId, index, doc_type, interval=30, displayFormat=None, esMode="search", defaultValue=None, mapping=None)
		while True:
			print("Searching " + self.stateId + " in index=" + self.esIndex + ", doc_type=" + self.esDocType + ", esMode=" + self.esMode)
			try:
				stateValue = fetchfromes.llReadFromES(self.esClient, self.stateId, self.esIndex, self.esDocType, self.esMode, 
													self.defaultValue, self.mapping)
				if stateValue is not None:
					if self.displayFormat is not None:
						stateValueStr = self.displayFormat % stateValue
					else:
						stateValueStr = json.dumps(stateValue)
					print("ES Fetch : " + self.stateId + "=" + stateValueStr + " (" + str(stateValue) + ")")
					# sweetHome.setState(self.stateId, stateValue)
					await self.controller.notifyStateUpdate(self.stateId, stateValue, stateValueStr)
			except Exception as err:
				print(" ! Caught " + str(err))
			await asyncio.sleep(self.interval)
	
	def modifyState(self, stateValue):
		fetchfromes.llWriteStateToES(self.esClient, stateId=self.getStateId(), index=self.esIndex, doc_type=self.esDocType, 
									esMode="get", stateValue=stateValue)
