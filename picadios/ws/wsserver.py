import json
import asyncio
import picadios.controller
import websockets

class WSServer(picadios.controller.StateUpdateNotifyHandler):
    wsClients = []
    sweetHome = None
    controller = None
    
    def __init__(self, sweetHome, controller):
        self.sweetHome = sweetHome
        self.controller = controller
        self.controller.registerStateUpdateNotifyHandler(handler=self)
    
    def startup(self):
        asyncio.get_event_loop().run_until_complete(websockets.serve(self.serveWebSocket, '0.0.0.0', 5455))
    
    async def serveWebSocket(self, websocket, path):
        global wsClients
        print ("Run at path : " + path)
        try:
            print ("websocket : " + str(websocket))
            self.wsClients.append(websocket)
            while True:
                message = await websocket.recv()
                if message is None:
                    # time.sleep(1)
                    await asyncio.sleep(0.5)
                    continue
                print ("Message : " + str(message))
                jsonMessage = json.loads(message)
                action = jsonMessage["msg"];
                print ("Action : [" + action + "]")
                if action == "login":
                    print("Sending Login OK")
                    response = {"msg":"login", "data":{"success":"true"}}
                    await websocket.send(json.dumps(response))
                elif action == "get_home":
                    print("Sending Home !")
                    jsonHome = self.sweetHome.getUpdatedHome()
                    response = {"msg":"get_home", "data":jsonHome}
                    await websocket.send(json.dumps(response))
                elif action == "set_state":
                    stateId = jsonMessage["data"]["id"]
                    stateValue = jsonMessage["data"]["value"]
                    self.controller.modifyState(stateId, stateValue)
                    
        finally:
            self.wsClients.remove(websocket)

    async def notifyStateUpdate(self, stateId, stateValue, stateValueStr):
        eventMessage = {"msg":"event", "data":{"event_raw":"io_changed id:" + stateId + " state:" + str(stateValue),
            "type":"3", "type_str":"io_changed", "data":{"id":stateId, "state":stateValueStr}}}
        for wsClient in self.wsClients:
            await wsClient.send(json.dumps(eventMessage))
