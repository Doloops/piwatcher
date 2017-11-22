import json

class Home():
    # Initial config as JSON object
    jsonHome = None
    
    # Item Configuration
    itemsConfiguration = {}
    
    def __init__(self):
        with open ("home.json") as homeFile:
            self.jsonHome = json.loads(homeFile.read())
        for room in self.jsonHome["home"]:
            for item in room["items"]:
                self.itemsConfiguration[item["id"]] = item
            
    def getItems(self):
        return self.itemsConfiguration
    
    def getHome(self):
        return self.jsonHome
