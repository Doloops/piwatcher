import RPi.GPIO as GPIO ## Import GPIO library
from datetime import datetime
import time
import subprocess
import re

currentLedStatus = False
disk_name="sda"

GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
GPIO.setup(11, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
GPIO.output(11,currentLedStatus) ## Turn on GPIO pin 7

GPIO.setup(5, GPIO.IN) # Switch

lastTotalIO = 0
previousDiskState = "unknown"
previousDiskStateTime = time.time()

def checkDiskActivity():
    global lastTotalIO
    try:
        stat_file = open("/sys/block/" + disk_name + "/stat", "r")
        line = stat_file.read().strip().split()
        readIO = int(line[0])
        writeIO = int(line[4])
        totalIO = readIO + writeIO
#            print("line readIO=" + str(readIO) + ", writeIO=" + str(writeIO) + ", totalIO=" + str(totalIO) + ", last=" + str(lastTotalIO))
        diskActivity = False
        if totalIO != lastTotalIO:
            diskActivity = True
        lastTotalIO = totalIO
        return diskActivity
    finally:
        stat_file.close()

def checkDiskState():
    result = subprocess.check_output(["hdparm", "-C", "/dev/" + disk_name], shell=False)
    result = result.decode("utf-8")
    pattern = re.compile("\n.*\n drive state is:  (.*)\n")
    match = pattern.match(result);
    state = match.group(1);
#    print("Result = [" + state + "]")
    if state == "active/idle":
        if checkDiskActivity():
            return "active"
        else:
            return "idle"
    elif state == "standby":
        return "standby"
    raise ValueError("Unknown disk state exception : [" + state + "]");

def updateDiskStateTime(diskState):
    global previousDiskState
    global previousDiskStateTime
    if diskState != previousDiskState:
        previousDiskStateTime = time.time()
        previousDiskState = diskState

try:
    while True:
        diskState = checkDiskState()
        updateDiskStateTime(diskState)
        if diskState == "active":
            currentLedStatus = not currentLedStatus
        else:
            currentLedStatus = True
#        state = GPIO.input(5)
        diskStateTime = time.time() - previousDiskStateTime
        print (str(datetime.now().time()) + ", diskState=" + diskState + " for " + str(int(diskStateTime)) + "s, currentLedStatus=" + str(currentLedStatus))
        GPIO.output(11, currentLedStatus)
        time.sleep(0.5)

finally:
    GPIO.cleanup()
