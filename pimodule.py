class PiModule:

    moduleName = "Unknown module"
    wrapMeasureIn = None
    piwatcher = None

    def __init__(self, moduleName):
        self.moduleName = moduleName

    def setPiWatcher(self, piwatcher):
        self.piwatcher = piwatcher

    def udpate(self, measure):
        raise NotImplementedError("Method update() for module " + self.moduleName + " not implemented !")
        
    def shutdown(self):
        raise NotImplementedError("Method shutdown() for module " + self.moduleName + " not implemented !")
        
    def getModuleName(self):
        return self.moduleName
    
    def getName(self):
        return self.getModuleName()

    def mayWrap(self, measure):
        if self.wrapMeasureIn is not None:
            wrapped = {}
            wrapped[self.wrapMeasureIn] = measure
            measure = wrapped
        return measure
