import json

class Home():
    # Initial config as JSON object
    jsonHome = None
    
    # Internal state
    internalStates = {}
    
    # Item Configuration
    itemsConfiguration = {}
    
    def __init__(self):
        with open ("home.json") as homeFile:
            self.jsonHome = json.loads(homeFile.read())
        for room in self.jsonHome["home"]:
            print("Room : " + room["name"])
            for item in room["items"]:
                self.itemsConfiguration[item["id"]] = item
            
    def getItems(self):
        return self.itemsConfiguration
    
    def getHome(self):
        return self.jsonHome
    
    def getUpdatedHome(self):
        jsonHome = self.getHome()
        for room in jsonHome["home"]:
            for item in room["items"]:
                if item["id"] in self.internalStates:
                    rawValue = self.internalStates[item["id"]]
                    if isinstance(rawValue, str):
                        itemValue = rawValue
                    elif "displayFormat" in item:
                        itemValue = item["displayFormat"] % rawValue
                    else:
                        itemValue = json.dumps(rawValue)
                    print("Update " + item["id"] + "=" + itemValue)
                    item["state"] = itemValue
        return jsonHome

    def setState(self, stateId, stateValue):
        self.internalStates[stateId] = stateValue
    
    def getState(self, stateId):
        if stateId not in self.internalStates:
            print ("No state " + stateId + "!")
            return None 
        return self.internalStates[stateId]
