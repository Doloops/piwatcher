'''
Utility class to monitor disk activity
'''
import re
import time
import RPi.GPIO as GPIO

class DiskWatcher:
    hdparmPattern = re.compile("\n.*\n drive state is:  (.*)\n")

    diskLedPinout = None
    lastTotalIO = 0
    previousDiskState = "unknown"
    previousDiskStateTime = time.time()
    ledPwm = None

    def __init__(self, diskLedPinout=None, diskDeviceName=None):
        self.diskLedPinout=diskLedPinout
        self.diskDeviceName=diskDeviceName
        GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
        GPIO.setup(diskLedPinout, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
        GPIO.output(diskLedPinout, False) ## Turn on GPIO pin 7
        self.ledPwm = GPIO.PWM(diskLedPinout, 0.5)
        self.ledPwm.start(25)

    def checkDiskActivity(self):
        try:
            stat_file = open("/sys/block/" + diskDeviceName + "/stat", "r")
            line = stat_file.read().strip().split()
            readIO = int(line[0])
            writeIO = int(line[4])
            totalIO = readIO + writeIO
            diskActivity = False
            if totalIO != self.lastTotalIO:
                diskActivity = True
            lastTotalIO = totalIO
            return diskActivity
        finally:
            stat_file.close()

    def checkDiskState(self):
        result = subprocess.check_output(["hdparm", "-C", "/dev/" + diskDeviceName], shell=False)
        result = result.decode("utf-8")
        match = hdparmPattern.match(result);
        state = match.group(1);
        if state == "active/idle":
            if checkDiskActivity():
                return "active"
            else:
                return "idle"
        elif state == "standby":
            return "standby"
        raise ValueError("Unknown disk state exception : [" + state + "]");

    def setLedFromDiskState(self, diskState):
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
        if diskState != previousDiskState:
            self.previousDiskStateTime = time.time()
            self.previousDiskState = diskState

    def shutdown(self):
        self.ledPwm.stop()
        GPIO.cleanup()

