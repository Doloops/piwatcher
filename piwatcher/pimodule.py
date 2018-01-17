class PiModule:

    name = "Unknown module"
    moduleName = "Unknown module"
    wrapMeasureIn = None
    piwatcher = None

    def __init__(self, moduleName):
        self.moduleName = moduleName
        self.name = moduleName

    def setPiWatcher(self, piwatcher):
        self.piwatcher = piwatcher

    def udpate(self, measure):
        raise NotImplementedError("Method update() for module " + self.moduleName + " not implemented !")
        
    def shutdown(self):
        raise NotImplementedError("Method shutdown() for module " + self.moduleName + " not implemented !")
        
    def getModuleName(self):
        return self.moduleName

    def getModuleClassName(self):
        return self.__class__.__module__ + "." + self.__class__.__name__
    
    def getName(self):
        return self.getName()

    def setName(self, name):
        self.name = name

    def mayWrap(self, measure):
        if self.wrapMeasureIn is not None:
            wrapped = {}
            wrapped[self.wrapMeasureIn] = measure
            measure = wrapped
        return measure
