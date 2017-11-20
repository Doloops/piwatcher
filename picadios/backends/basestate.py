import json

class BaseState:
    stateId = None
    displayFormat = None
    defaultValue = None
    mapping = None
    itemType = None
    controller = None

    def __init__(self, controller, item):
        self.controller = controller
        self.stateId = item["id"]
        if "displayFormat" in item:
            self.displayFormat = item["displayFormat"]
        if "state" in item:
            self.defaultValue = json.loads(item["state"])
        if "mapping" in item:
            self.mapping = item["mapping"]
        if "var_type" in item:
            self.itemType = item["var_type"]

    def getStateId(self):
        return self.stateId
