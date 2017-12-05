import json
import asyncio
import picadios.controller
import websockets
import logging

logger = logging.getLogger("picadios.wsserver")

class WSServer(picadios.controller.StateUpdateNotifyHandler):
    wsClients = []
    controller = None
    wsConfig = None
    
    def __init__(self, controller, wsConfig):
        self.controller = controller
        self.wsConfig = wsConfig
        self.controller.registerStateUpdateNotifyHandler(handler=self)
    
    def startup(self):
        asyncio.get_event_loop().run_until_complete(websockets.serve(self.serveWebSocket, self.wsConfig["host"], self.wsConfig["port"]))
    
    def doLogin(self, cn_user, cn_pass):
        for user in self.wsConfig["users"]:
            if user["user"] == cn_user and user["pass"] == cn_pass:
                logger.info("Authenticated as : " + user["user"])
                return True
        logger.error("Could not authenticate : " + cn_user)
        return False
    
    async def serveWebSocket(self, websocket, path):
        global wsClients
        logger.info("Run at path : " + path)
        authenticated = False
        try:
            self.wsClients.append(websocket)
            while True:
                message = await websocket.recv()
                if message is None:
                    # time.sleep(1)
                    await asyncio.sleep(0.5)
                    continue
                logger.debug("Message : " + str(message))
                jsonMessage = json.loads(message)
                action = jsonMessage["msg"];
                if action == "login":
                    logger.info("Received auth info : " + str(jsonMessage))
                    cn_user = jsonMessage["data"]["cn_user"]
                    cn_pass = jsonMessage["data"]["cn_pass"]
                    authenticated = self.doLogin(cn_user, cn_pass)
                    logger.debug("Sending Login Result : " + str(authenticated))
                    response = {"msg":"login", "data":{"success":json.dumps(authenticated)}}                    
                    await websocket.send(json.dumps(response))
                if not authenticated:
                    logger.error("Not authenticated ! dropping connection !")
                    return
                if action == "get_home":
                    logger.debug("Sending Home !")
                    jsonHome = self.controller.getUpdatedHome()
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
