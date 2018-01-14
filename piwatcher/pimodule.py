class PiModule:

    moduleClass = "Unknown module"
    moduleName = "Unknown module"
    wrapMeasureIn = None
    piwatcher = None

    def __init__(self, moduleName):
        self.moduleName = moduleName
        self.moduleClass = self.__class__

    def setPiWatcher(self, piwatcher):
        self.piwatcher = piwatcher

    def udpate(self, measure):
        raise NotImplementedError("Method update() for module " + self.moduleName + " not implemented !")
        
    def shutdown(self):
        raise NotImplementedError("Method shutdown() for module " + self.moduleName + " not implemented !")
        
    def getModuleName(self):
        return self.moduleName

    def getModuleClassName(self):
        return self.moduleClass.__module__ + "." + self.moduleClass.__name__
    
    def getName(self):
        return self.getModuleName()

    def mayWrap(self, measure):
        if self.wrapMeasureIn is not None:
            wrapped = {}
            wrapped[self.wrapMeasureIn] = measure
            measure = wrapped
        return measure
