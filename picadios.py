import time

import asyncio
import websockets
import elasticsearch
import fetchfromes

import logging
from elasticsearch.exceptions import NotFoundError
logger = logging.getLogger('websockets.server')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

import json


wsClients = []
esClient = elasticsearch.Elasticsearch([{"host":"osmc"}])

# Internal state
internalStates = {}
itemsConfiguration = {}

def getHome():
    with open ("home.json") as homeFile:
        jsonHome = json.loads(homeFile.read())
        return jsonHome

def getUpdatedHome():
    global internalStates
    jsonHome = getHome()
    for room in jsonHome["home"]:
        for item in room["items"]:
            if item["id"] in internalStates:
                rawValue = internalStates[item["id"]]
                if isinstance(rawValue, str):
                    itemValue = rawValue
                elif "displayFormat" in item:
                    itemValue = item["displayFormat"] % rawValue
                else:
                    itemValue = json.dumps(rawValue)
                print("Update " + item["id"] + "=" + itemValue)
                item["state"] = itemValue
    return jsonHome

def mayUpdateItem(stateId, stateValue):
    global itemsConfiguration
    global esClient
    if stateId in itemsConfiguration:
        item = itemsConfiguration[stateId]
        if "es" in item and "es_mode" in item["es"] and item["es"]["es_mode"] == "get":
            fetchfromes.llWriteStateToES(esClient, stateId=item["id"], index=item["es"]["index"], doc_type=item["es"]["doc_type"],
                           esMode="get", stateValue = stateValue)

async def setState(stateId, stateValue):
    global internalStates
    global wsClients
    if stateId in internalStates:
        value = internalStates[stateId]
        if isinstance(value, bool):
            value = not value
            internalStates[stateId] = value
        elif isinstance(internalStates[stateId], int) or isinstance(internalStates[stateId], float):
            if stateValue == "inc":
                value = value + 1
            elif stateValue == "dec":
                value = value - 1
            else:
                print ("Invalid value for int :" + str(value))
                raise ValueError("Invalid value for int :" + str(value))
            internalStates[stateId] = value
        else:
            print ("Value not supported for stateId : " + stateId)
            raise ValueError("Value not supported for stateId : " + stateId)
        mayUpdateItem(stateId, value)
        valueStr = json.dumps(value);
        print("Updated " + stateId + "=" + valueStr)
        eventMessage = {"msg":"event","data":{"event_raw":"io_changed id:" + stateId + " state:" + valueStr,
            "type":"3","type_str":"io_changed","data":{"id":stateId,"state":valueStr}}}
        for wsClient in wsClients:
            await wsClient.send(json.dumps(eventMessage))
    else:
        print("State not in internalStates : " + stateId)

async def serveWebSocket(websocket, path):
    global wsClients
    print ("Run at path : " + path)
    try:
        print ("websocket : " + str(websocket))
        wsClients.append(websocket)
        while True:
            message = await websocket.recv()
            if message is None:
                time.sleep(1)
                continue
            print ("Message : " + str(message))
            jsonMessage = json.loads(message)
            action = jsonMessage["msg"];
            print ("Action : [" + action + "]")
            if action == "login":
                print("Sending Login OK")
                response = {"msg":"login","data":{"success":"true"}}
                await websocket.send(json.dumps(response))
            elif action == "get_home":
                print("Sending Home !")
                jsonHome = getUpdatedHome()
                response = {"msg":"get_home", "data":jsonHome}
                await websocket.send(json.dumps(response))
            elif action == "set_state":
                stateId = jsonMessage["data"]["id"]
                stateValue = jsonMessage["data"]["value"]
                await setState(stateId, stateValue)
                
    finally:
        wsClients.remove(websocket)

print ("Running now !")

asyncio.get_event_loop().run_until_complete(
   websockets.serve(serveWebSocket, '0.0.0.0', 5455))


async def periodicStateUpdate(esClient, stateId, index, doc_type, interval = 30, displayFormat = None, esMode = "search", defaultValue = None, mapping = None):
    global wsClients
    global internalStates
#    hostName=idParts[0]
#    valueName=idParts[1]
    while True:
        # print("Searching " + stateId + " in index=" + index + ", doc_type=" + doc_type + ", esMode=" + esMode)
        stateValue = fetchfromes.llReadFromES(esClient, stateId, index, doc_type, esMode, defaultValue, mapping)
        if stateValue is not None:
            if displayFormat is not None:
                stateValueStr = displayFormat % stateValue
            else:
                stateValueStr = json.dumps(stateValue)

            print("Got " + stateId + "=" + stateValueStr + " (" + str(stateValue) + ")")
            internalStates[stateId] = stateValue

            eventMessage = {"msg":"event","data":{"event_raw":"io_changed id:" + stateId + " state:" + str(stateValue),
                "type":"3","type_str":"io_changed","data":{"id":stateId,"state":stateValueStr}}}
            for wsClient in wsClients:
                await wsClient.send(json.dumps(eventMessage))
        await asyncio.sleep(interval)

jsonHome = getHome()
for room in jsonHome["home"]:
    print("Room : " + room["name"])
    for item in room["items"]:
        itemsConfiguration[item["id"]] = item
        if "es" in item:
            print("Configuring item " + item["id"])
            displayFormat = None
            if "displayFormat" in item:
                displayFormat = item["displayFormat"]
            esMode = "search"
            if "es_mode" in item["es"]:
                esMode = item["es"]["es_mode"]
            defaultValue = None
            if "state" in item:
                defaultValue = json.loads(item["state"])
            mapping = None
            if "mapping" in item:
                mapping = item["mapping"]
            asyncio.get_event_loop().create_task(
                periodicStateUpdate(esClient, stateId=item["id"], index=item["es"]["index"], doc_type=item["es"]["doc_type"], 
                                    displayFormat=displayFormat, esMode=esMode, defaultValue=defaultValue, mapping=mapping))
        elif item["type"] == "InternalBool":
            internalStates[item["id"]] = json.loads(item["state"])
            print("Configuring item " + item["id"] + "=" + str(internalStates[item["id"]]))
            if not isinstance(internalStates[item["id"]], bool):
                print("Error ! item is not a boolean !!!")
        elif item["type"] == "InternalInt":
            internalStates[item["id"]] = json.loads(item["state"])
            print("Configuring item " + item["id"] + "=" + str(internalStates[item["id"]]))
            if not isinstance(internalStates[item["id"]], int):
                print("Error ! item is not an integer !!!")


print("Run forever !")
asyncio.get_event_loop().run_forever()

print ("Finished !")


