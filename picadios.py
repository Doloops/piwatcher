import sys
import time

import asyncio
import signal
import websockets
import elasticsearch

import logging
logger = logging.getLogger('websockets.server')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

import pprint
import json


wsClients = []
es = elasticsearch.Elasticsearch([{"host":"osmc"}])

# Internal state
picadily = {}

def getHome():
    with open ("home.json") as homeFile:
        jsonHome = json.loads(homeFile.read())
        return jsonHome

def getUpdatedHome():
    global picadily
    jsonHome = getHome()
    for room in jsonHome["home"]:
        for item in room["items"]:
            if item["id"] in picadily:
                rawValue = picadily[item["id"]]
                if isinstance(rawValue, str):
                    itemValue = rawValue
                else:
                    itemValue = json.dumps(rawValue)
                print("Update " + item["id"] + "=" + itemValue)
                item["state"] = itemValue
    return jsonHome
                    
async def serveWebSocket(websocket, path):
    global wsClients
    global picadily
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
                if stateId in picadily:
                    value = picadily[stateId]
                    if isinstance(value, bool):
                        value = not value
                        picadily[stateId] = value
                    elif isinstance(picadily[stateId], int) or isinstance(picadily[stateId], float):
                        if stateValue == "inc":
                            value = value + 1
                        elif stateValue == "dec":
                            value = value - 1
                        else:
                            raise ValueError("Invalid value for int :" + value)
                        picadily[stateId] = value
                    else:
                        print ("Value not supported for stateId : " + stateId)
                        raise ValueError("Value not supported for stateId : " + stateId)
                    valueStr = json.dumps(value);
                    print("Updated " + stateId + "=" + valueStr)
                    eventMessage = {"msg":"event","data":{"event_raw":"io_changed id:" + stateId + " state:" + valueStr,
                        "type":"3","type_str":"io_changed","data":{"id":stateId,"state":valueStr}}}
                    for wsClient in wsClients:
                        await wsClient.send(json.dumps(eventMessage))                            
                else:
                    print("State not in picadily : " + stateId)
                
    finally:
        wsClients.remove(websocket)

print ("Running now !")

asyncio.get_event_loop().run_until_complete(
   websockets.serve(serveWebSocket, '0.0.0.0', 5455))
   
async def getTemp(esClient, tempId, index, doc_type, interval = 30):
    global wsClients
    global picadily
    tempValue = 0
    idParts = tempId.split('.')
    hostName=idParts[0]
    valueName=idParts[1]
    while True:
        query = {"query": {"bool": {"must": {"match_all":{}}}}, "sort":[{"timestamp":{"order":"desc"}}]}
        esResult = esClient.search(index=index, doc_type=doc_type, body = query)
#        print("esResult=" + str(esResult))
        if esResult["hits"]["total"] < 1:
            print("No result !")
            continue
        tempValue = esResult["hits"]["hits"][0]["_source"][hostName][valueName]
        tempValueStr = "%.2f" % tempValue
        print("Got " + hostName + "." + valueName + "=" + tempValueStr + " (" + str(tempValue) + ")")
        picadily[tempId] = tempValueStr
        
        eventMessage = {"msg":"event","data":{"event_raw":"io_changed id:" + tempId + " state:" + str(tempValue),
            "type":"3","type_str":"io_changed","data":{"id":tempId,"state":tempValueStr}}}
        for wsClient in wsClients:
            await wsClient.send(json.dumps(eventMessage))
        await asyncio.sleep(interval)

jsonHome = getHome()
for room in jsonHome["home"]:
    print("Room : " + room["name"])
    for item in room["items"]:
        if "es" in item:
            print("Configuring item " + item["id"])
            asyncio.get_event_loop().create_task(
                getTemp(es, tempId=item["id"], index=item["es"]["index"], doc_type=item["es"]["doc_type"]))
        elif item["type"] == "InternalBool":
            picadily[item["id"]] = json.loads(item["state"])
            print("Configuring item " + item["id"] + "=" + str(picadily[item["id"]]))
            if not isinstance(picadily[item["id"]], bool):
                print("Error ! item is not a boolean !!!")
        elif item["type"] == "InternalInt":
            picadily[item["id"]] = json.loads(item["state"])
            print("Configuring item " + item["id"] + "=" + str(picadily[item["id"]]))
            if not isinstance(picadily[item["id"]], int):
                print("Error ! item is not an integer !!!")


print("Run forever !")
asyncio.get_event_loop().run_forever()

print ("Finished !")



### GARBAGE

if False:
    asyncio.get_event_loop().create_task(
        getTemp(es, tempId='oswh_osmc/sys-measure/osmc/indoorTemp', index="oswh-osmc", doc_type="sys-measure", hostName="osmc", valueName="indoorTemp"))

    asyncio.get_event_loop().create_task(
        getTemp(es, tempId='input_1', index="oswh-pizero1", doc_type="sys-measure", hostName="pizero1", valueName="indoorTemp"))

    asyncio.get_event_loop().create_task(
        getTemp(es, tempId='input_2', index="oswh-pizero2", doc_type="sys-measure", hostName="pizero2", valueName="indoorTemp"))

    asyncio.get_event_loop().create_task(
        getTemp(es, tempId='input_4', index="oswh-owm-sartrouville", doc_type="openweathermap", hostName="main", valueName="temp"))

