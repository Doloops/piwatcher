class PiModule:

    moduleName = "Unknown module"
    wrapMeasureIn = None

    def __init__(self, moduleName):
        self.moduleName = moduleName

    def udpate(self, measure):
        raise NotImplementedError("Method update() for module " + moduleName + " not implemented !")
        
    def shutdown(self):
        raise NotImplementedError("Method shutdown() for module " + moduleName + " not implemented !")
        
    def getModuleName(self):
        return self.moduleName

    def mayWrap(self, measure):
        if self.wrapMeasureIn is not None:
            wrapped = {}
            wrapped[self.wrapMeasureIn] = measure
            measure = wrapped
        return measure
