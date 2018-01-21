'''
Utility class to monitor disk activity
'''
from piwatcher import pimodule
import re
import time
import subprocess

class DiskWatcher(pimodule.PiModule):
    hdparmPattern = re.compile("\n.*\n drive state is:  (.*)\n")

    diskLedPinout = None
    diskDeviceName = None
    lastTotalIO = 0
    previousDiskState = "unknown"
    previousDiskStateTime = time.time()
    useMeasurePerDisk = True

    hasGPIO = False
    ledPwm = None

    def __init__(self, config):
        pimodule.PiModule.__init__(self,"Disk")
        self.diskDeviceName = config["deviceName"]

        if "ledPinout" in config:    
            self.diskLedPinout = config["ledPinout"]

            import RPi.GPIO as GPIO
            hasGPIO = True
            GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
            GPIO.setup(self.diskLedPinout, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
            GPIO.output(self.diskLedPinout, False) ## Turn on GPIO pin 7
            self.ledPwm = GPIO.PWM(self.diskLedPinout, 0.5)
            self.ledPwm.start(25)
        if "useMeasurePerDisk" in config:
            self.useMeasurePerDisk = config["useMeasurePerDisk"]

    def checkDiskActivity(self):
        try:
            stat_file = open("/sys/block/" + self.diskDeviceName + "/stat", "r")
            line = stat_file.read().strip().split()
            readIO = int(line[0])
            writeIO = int(line[4])
            totalIO = readIO + writeIO
            diskActivity = False
            if totalIO != self.lastTotalIO:
                diskActivity = True
            self.lastTotalIO = totalIO
            return diskActivity
        finally:
            stat_file.close()

    def checkDiskState(self):
        result = subprocess.check_output(["hdparm", "-C", "/dev/" + self.diskDeviceName], shell=False)
        result = result.decode("utf-8")
        match = self.hdparmPattern.match(result);
        state = match.group(1);
        if state == "active/idle":
            if self.checkDiskActivity():
                return "active"
            else:
                return "idle"
        elif state == "standby":
            return "standby"
        raise ValueError("Unknown disk state exception : [" + state + "]");

    def setLedFromDiskState(self, diskState):
        if self.ledPwm is None:
            return
        if diskState == "active":
            self.ledPwm.ChangeFrequency(4)
            self.ledPwm.ChangeDutyCycle(50)
        elif diskState == "idle":
            self.ledPwm.ChangeFrequency(0.5)
            self.ledPwm.ChangeDutyCycle(50)
        else:
            self.ledPwm.ChangeFrequency(0.5)
            self.ledPwm.ChangeDutyCycle(100)        

    def updateDiskStateTime(self, diskState):
        if diskState != self.previousDiskState:
            self.previousDiskStateTime = time.time()
            self.previousDiskState = diskState
        return self.previousDiskStateTime

    def update(self, measure):
        now = time.time()
        diskState = self.checkDiskState()
        self.setLedFromDiskState(diskState)
        previousDiskStateTime = self.updateDiskStateTime(diskState)
        cumulateDiskStateTime = now - previousDiskStateTime
        if self.useMeasurePerDisk:
            diskMeasure = {}
            measure[self.diskDeviceName] = diskMeasure
        else:
            diskMeasure = measure
        diskMeasure["diskState"] = diskState
        diskMeasure["cumulateDiskStateTime"] = cumulateDiskStateTime
        diskStateMessage = ", " + self.diskDeviceName + "=" + diskState + " for " + str(int(cumulateDiskStateTime)) + "s"
        print(diskStateMessage, end='')

    def shutdown(self):
        print("Shutdown " + self.getModuleName())
        self.ledPwm.stop()
        if self.hasGPIO:
            GPIO.cleanup()
