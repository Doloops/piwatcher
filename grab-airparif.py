import elasticsearch
import json
from datetime import datetime
import http

# http://www.airparif.asso.fr/appli/api/indice?date=jour

airparifUrlHost = "www.airparif.asso.fr";
airparifUrlPath = "/appli/api/indice?date=jour"

es = elasticsearch.Elasticsearch(hosts=[{"host":"pizero3"},{"host":"192.168.1.63"},{"host":"osmc"}])

def getPollutionResult():
    print("Calling URL : " + airparifUrlHost + airparifUrlPath)


    headers = { "User-Agent": "Mozilla/5.0" }

    httpConn = http.client.HTTPConnection(airparifUrlHost)
    httpConn.request("GET", airparifUrlPath, headers = headers)
    httpRes = httpConn.getresponse()
    if httpRes.status != 200:
        raise ValueError("Invalid HTTP result " + str(httpRes.status) + ":" + httpRes.reason)
    data = httpRes.read()
    return data.decode("utf-8")

pollutionResult = getPollutionResult()
# weatherResult = getWeatherResult(owmUrlHost, owmUrlPath)
jsonResult = json.loads(pollutionResult)

# jsonResult["timestamp"] = datetime.utcnow().timestamp()
timestamp = datetime.utcnow().isoformat()
uniqueId = "airparif-" + timestamp

finalJson = { "timestamp": timestamp, "hier": jsonResult[0]["indice"], "jour": jsonResult[1]["indice"], "demain": jsonResult[2]["indice"] }

print("uniqueId=" + uniqueId + ", timestamp=" + timestamp)

print("jsonResult=" + str(finalJson))

es.index(index="oswh-airparif", doc_type="airparif", id=uniqueId, body=finalJson)

