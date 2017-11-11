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
                with open ("home.json") as homeFile:
                    jsonHome = json.loads(homeFile.read())
                response = {"msg":"get_home", "data":jsonHome}
                await websocket.send(json.dumps(response))
    finally:
        wsClients.remove(websocket)

print ("Running now !")

asyncio.get_event_loop().run_until_complete(
   websockets.serve(serveWebSocket, '0.0.0.0', 5455))
   
async def getTemp(esClient, tempId, index, doc_type, hostName, valueName, interval = 5):
    global wsClients
    tempValue = 0
    while True:
        await asyncio.sleep(interval)
        query = {"query": {"bool": {"must": {"match_all":{}}}}, "sort":[{"timestamp":{"order":"desc"}}]}
        esResult = esClient.search(index=index, doc_type=doc_type, body = query)
#        print("esResult=" + str(esResult))
        if esResult["hits"]["total"] < 1:
            print("No result !")
            continue
        tempValue = esResult["hits"]["hits"][0]["_source"][hostName][valueName]
        tempValueStr = "%.2f" % tempValue
        print("Got " + hostName + "." + valueName + "=" + tempValueStr + " (" + str(tempValue) + ")")
        
        eventMessage = {"msg":"event","data":{"event_raw":"io_changed id:" + tempId + " state:" + str(tempValue),
            "type":"3","type_str":"io_changed","data":{"id":tempId,"state":tempValueStr}}}
        for wsClient in wsClients:
            await wsClient.send(json.dumps(eventMessage))

asyncio.get_event_loop().create_task(
    getTemp(es, tempId='input_0', index="oswh-osmc", doc_type="sys-measure", hostName="osmc", valueName="indoorTemp"))

asyncio.get_event_loop().create_task(
    getTemp(es, tempId='input_1', index="oswh-pizero1", doc_type="sys-measure", hostName="pizero1", valueName="indoorTemp"))

asyncio.get_event_loop().create_task(
    getTemp(es, tempId='input_2', index="oswh-pizero2", doc_type="sys-measure", hostName="pizero2", valueName="indoorTemp"))

asyncio.get_event_loop().create_task(
    getTemp(es, tempId='input_4', index="oswh-owm-sartrouville", doc_type="openweathermap", hostName="main", valueName="temp"))


print("Run forever !")
asyncio.get_event_loop().run_forever()

print ("Finished !")

