import asyncio
import json
import logging

logger = logging.getLogger("picadios.controller")

class StateUpdateNotifyHandler:
    async def notifyStateUpdate(self, stateId, stateValue, stateValueStr):
        pass

class Controller(StateUpdateNotifyHandler):
    
    sweetHome = None
    
    def __init__(self, sweetHome):
        logging.info("Starting new Controller")
        self.sweetHome = sweetHome 
    
    async def modifyState(self, stateId, stateValue):
        logging.debug("* modifyState : " + stateId + "=" + stateValue)
        value = await self.getState(stateId)
        logging.debug("** type(value)=" + str(type(value)))
        if value is None:
            logger.debug("State not in internalStates : " + stateId)
            return
        if isinstance(value, bool):
            if stateValue.lower() == "false":
                value = False
            elif stateValue.lower() == "true":
                value = True
            else:
                logger.debug("State not a valid bool " + value)
                return                
        elif isinstance(value, int) or isinstance(value, float):
            if stateValue == "inc":
                value = value + 1
            elif stateValue == "dec":
                value = value - 1
            else:
                logger.error("Invalid value for int :" + str(value))
                raise ValueError("Invalid value for int :" + str(value))
        else:
            logger.error("Value not supported for stateId : " + stateId)
            raise ValueError("Value not supported for stateId : " + stateId)
        
        # self.sweetHome.setState(stateId, value)
        # mayUpdateItem(stateId, value)
        if stateId in self.backendHandlers:
            await self.backendHandlers[stateId].modifyState(value)
        else:
            logger.debug("Not a registered backend handler : " + stateId)
        valueStr = json.dumps(value);
        logger.debug("Updated " + stateId + "=" + valueStr + " (raw=" + str(value) + ", type=" + str(type(value)) + ")")

    async def getState(self, stateId):
        if stateId in self.backendHandlers:
            return await self.backendHandlers[stateId].getState()
        return None

    async def getUpdatedHome(self):
        jsonHome = self.sweetHome.getHome()
        for room in jsonHome["home"]:
            for item in room["items"]:
                itemId = item["id"]
                itemValue = await self.getState(itemId)
                logger.debug("getUpdatedHome() : itemId=" + itemId + ", itemValue=" + str(itemValue))
                if itemValue is not None:
                    if isinstance(itemValue, str):
                        pass
                    elif "displayFormat" in item:
                        itemValue = item["displayFormat"] % itemValue
                    else:
                        itemValue = json.dumps(itemValue)
                    logger.debug("Update " + item["id"] + "=" + itemValue)
                    item["state"] = itemValue
        return jsonHome

    stateUpdateNotifyHandlers = []
    backendHandlers = {}
    
    def registerStateUpdateNotifyHandler(self, handler):
        self.stateUpdateNotifyHandlers.append(handler)
        
    async def notifyStateUpdate(self, stateId, stateValue, stateValueStr):
#        self.sweetHome.setState(stateId, stateValue)
        for handler in self.stateUpdateNotifyHandlers:
            await handler.notifyStateUpdate(stateId, stateValue, stateValueStr)

    def registerBackendState(self, backendHandler):
        self.backendHandlers[backendHandler.getStateId()] = backendHandler
        asyncio.get_event_loop().create_task(backendHandler.asyncUpdate())
