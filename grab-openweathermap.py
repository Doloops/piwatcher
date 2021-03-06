import elasticsearch
import json
from datetime import datetime
import http
from os.path import expanduser

# http://api.openweathermap.org/data/2.5/weather?id=6444080&appid=26c230c3790ffb70be53053a90882a7e&units=metric

owmUrlHost = "api.openweathermap.org";

es = elasticsearch.Elasticsearch(hosts=[{"host":"pizero3"},{"host":"banane"},{"host":"osmc"}])

def getConfig():
    with open(expanduser("~") + "/.openweathermap/config.json") as confFile:
        confString = confFile.read()
#        print("CONF=" + confString)
        return json.loads(confString)


def forgeOWMUrlPath(jsonConfig):
    return "/data/2.5/weather?id=" + jsonConfig["cityId"] + "&appId=" + jsonConfig["appId"] + "&units=metric"

def getWeatherResult(owmUrlHost, owmUrlPath):
    print("Calling URL : " + owmUrlHost + owmUrlPath)

    httpConn = http.client.HTTPConnection(owmUrlHost)
    httpConn.request("GET", owmUrlPath)
    httpRes = httpConn.getresponse()
    if httpRes.status != 200:
        raise ValueError("Invalid HTTP result " + str(httpRes.status) + ":" + httpRes.reason)
    data = httpRes.read()
    return data.decode("utf-8")

def getWeatherResult_Static():
    return "{\"coord\":{\"lon\":2.18,\"lat\":48.95},\"weather\":[{\"id\":701,\"main\":\"Mist\",\"description\":\"mist\",\"icon\":\"50n\"},{\"id\":741,\"main\":\"Fog\",\"description\":\"fog\",\"icon\":\"50n\"}],\"base\":\"stations\",\"main\":{\"temp\":11.57,\"pressure\":1021,\"humidity\":93,\"temp_min\":10,\"temp_max\":12},\"visibility\":6000,\"wind\":{\"speed\":1.5,\"deg\":70},\"clouds\":{\"all\":88},\"dt\":1506488400,\"sys\":{\"type\":1,\"id\":5610,\"message\":0.2337,\"country\":\"FR\",\"sunrise\":1506491127,\"sunset\":1506533876},\"id\":6444080,\"name\":\"Sartrouville\",\"cod\":200}"

jsonConfig = getConfig()
# print("jsonConfig :" + str(jsonConfig))
owmUrlPath = forgeOWMUrlPath(jsonConfig)

# weatherResult = getWeatherResult_Static()
weatherResult = getWeatherResult(owmUrlHost, owmUrlPath)
jsonResult = json.loads(weatherResult)

# jsonResult["timestamp"] = datetime.utcnow().timestamp()
timestamp = datetime.utcnow().isoformat()
dt_date = datetime.utcfromtimestamp(jsonResult["dt"]).isoformat()
jsonResult["timestamp"] = timestamp;
jsonResult["dt_date"] = dt_date;
uniqueId = jsonConfig["cityId"] + "-" + str(jsonResult["dt"]) + "-" + timestamp
print("uniqueId=" + uniqueId + ", timestamp=" + timestamp + ", dt=" + str(jsonResult["dt"]) + ", temp=" + str(jsonResult["main"]["temp"]))

print("jsonResult=" + str(jsonResult))

es.index(index="oswh-owm-sartrouville", doc_type="openweathermap", id=uniqueId, body=jsonResult)

