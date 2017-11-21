import asyncio
import json

class StateUpdateNotifyHandler:
    async def notifyStateUpdate(self, stateId, stateValue, stateValueStr):
        None

class Controller(StateUpdateNotifyHandler):
    
    sweetHome = None
    
    def __init__(self, sweetHome):
        print("Starting new Controller")
        self.sweetHome = sweetHome 
    
    def modifyState(self, stateId, stateValue):
        print("* modifyState : " + stateId + "=" + stateValue)
        value = self.sweetHome.getState(stateId)
        if value is None:
            print("State not in internalStates : " + stateId)
            return
        if isinstance(value, bool):
            if stateValue.lower() == "false":
                value = False
            elif stateValue.lower() == "true":
                value = True
            else:
                print("State not a valid bool " + value)
                return                
        elif isinstance(value, int) or isinstance(value, float):
            if stateValue == "inc":
                value = value + 1
            elif stateValue == "dec":
                value = value - 1
            else:
                print ("Invalid value for int :" + str(value))
                raise ValueError("Invalid value for int :" + str(value))
        else:
            print ("Value not supported for stateId : " + stateId)
            raise ValueError("Value not supported for stateId : " + stateId)
        
        self.sweetHome.setState(stateId, value)
        # mayUpdateItem(stateId, value)
        if stateId in self.backendHandlers:
            self.backendHandlers[stateId].modifyState(value)
        valueStr = json.dumps(value);
        print("Updated " + stateId + "=" + valueStr + " (raw=" + str(value) + ", type=" + str(type(value)) + ")")

    stateUpdateNotifyHandlers = []
    backendHandlers = {}
    
    def registerStateUpdateNotifyHandler(self, handler):
        self.stateUpdateNotifyHandlers.append(handler)
        
    async def notifyStateUpdate(self, stateId, stateValue, stateValueStr):
        self.sweetHome.setState(stateId, stateValue)
        for handler in self.stateUpdateNotifyHandlers:
            await handler.notifyStateUpdate(stateId, stateValue, stateValueStr)

    def registerBackendState(self, backendHandler):
        self.backendHandlers[backendHandler.getStateId()] = backendHandler
        asyncio.get_event_loop().create_task(backendHandler.asyncUpdate())
