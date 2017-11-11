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
   
async def getTemp(temp, path):
    global wsClients
    global es
    tempValue = 0
    while True:
        print ("Run for temp:" + temp + ", path=" + path)
        await asyncio.sleep(1)
        query = {"query": {"bool": {"must": {"match_all":{}}}}, "sort":[{"timestamp":{"order":"desc"}}]}
        esResult = es.search(index="oswh-osmc", doc_type="sys-measure", body = query)
#        print("esResult=" + str(esResult))
        if esResult["hits"]["total"] < 1:
            print("No result !")
            continue
        tempValue = esResult["hits"]["hits"][0]["_source"]["osmc"]["indoorTemp"]
        print("indoorTemp=" + str(tempValue))
        tempValueStr = "%.2f" % tempValue
        eventMessage = {"msg":"event","data":{"event_raw":"io_changed id:" + temp + " state:" + str(tempValue),
            "type":"3","type_str":"io_changed","data":{"id":temp,"state":tempValueStr}}}
        for wsClient in wsClients:
            await wsClient.send(json.dumps(eventMessage))

asyncio.get_event_loop().create_task(getTemp('input_0', '123'))

print("Run forever !")
asyncio.get_event_loop().run_forever()

print ("Finished !")
      
#        await websocket.send(message)
    
#    websocket.ensure_open()
#    while True:
#        message = await websocket.read_message()
#        print ("Message : " + str(message))
#        pprint.pprint(message)
#        time.sleep(1)
#    async for message in websocket:
#        await websocket.send(message)

#async def echo(websocket, path):
#    while True:
#        try:
#            msg = await websocket.recv()
#        except websockets.ConnectionClosed:
#            pass
#        else:
#            await websocket.send(msg)

#async def echo_server(stop):
#    async with websockets.serve(echo, '0.0.0.0', 5455):
#        await stop

#loop = asyncio.get_event_loop()

# The stop condition is set when receiving SIGTERM.
#stop = asyncio.Future()
# loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

# Run the server until the stop condition is met.
#loop.run_until_complete(echo_server(stop))


