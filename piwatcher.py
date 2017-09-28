import RPi.GPIO as GPIO ## Import GPIO library
from datetime import datetime
import time
import subprocess
import re
import elasticsearch
import bmp280

ledPinout = 11
disk_name="sda"
statsInterval = 5

hdparmPattern = re.compile("\n.*\n drive state is:  (.*)\n")
cpuTempPattern = re.compile("temp=(.*)'C")

lastTotalIO = 0
previousDiskState = "unknown"
previousDiskStateTime = time.time()

es = elasticsearch.Elasticsearch()


tempSensorBmp280 = bmp280.BMP280()
chip_id, chip_version = tempSensorBmp280.read_id()

if chip_id == 88:
	tempSensorBmp280.reg_check()
else:
    raise ValueError ("Unsupported chip : " + chip_id)


GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
GPIO.setup(ledPinout, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
GPIO.output(ledPinout, False) ## Turn on GPIO pin 7

ledPwm = GPIO.PWM(ledPinout, 0.5)
ledPwm.start(25)

# GPIO.setup(5, GPIO.IN) # Switch
#        state = GPIO.input(5)


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
    match = hdparmPattern.match(result);
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

def getCPUTemp():
    result = subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_temp"], shell=False).decode("utf-8")
    match = cpuTempPattern.match(result)
    temp = float(match.group(1))
    return temp    

def getCPULoad():
    try:
        loadavg_file = open("/proc/loadavg")
        line = loadavg_file.read().strip().split()
        cpuLoad = float(line[0])
        return cpuLoad
    finally:
        loadavg_file.close()


try:
    while True:
        diskState = checkDiskState()
        updateDiskStateTime(diskState)
        if diskState == "active":
            ledPwm.ChangeFrequency(4)
            ledPwm.ChangeDutyCycle(50)
        elif diskState == "idle":
            ledPwm.ChangeFrequency(0.5)
            ledPwm.ChangeDutyCycle(50)
        else:
            ledPwm.ChangeFrequency(0.5)
            ledPwm.ChangeDutyCycle(100)        

#        currentLedStatus = not currentLedStatus
#        currentLedStatus = True
#        GPIO.output(11, currentLedStatus)
            
        diskStateTime = time.time() - previousDiskStateTime
        tnow = time.strftime("%Y%m%d-%H%M%S")
        cpuTemp = getCPUTemp()
        cpuLoad = getCPULoad()
        
        temperature, pressure = tempSensorBmp280.read()

        print (tnow + ", diskState=" + diskState + " for " + str(int(diskStateTime)) + "s, cpuTemp=" + str(cpuTemp) + ", load=" + str(cpuLoad)+ ", temp=" + ("%2.2f'C" % temperature) + ", pressure=" + ("%5.4f mbar" % pressure))
        try:
            es.index(index="oswh", doc_type="measure", id=tnow, body={"timestamp": datetime.utcnow(), "diskState": diskState, "cumulateDiskStateTime": diskStateTime, "cpuTemp": cpuTemp, "cpuLoad": cpuLoad, "indoorTemp": temperature, "indoorPressure": pressure, "statsInterval": statsInterval})
        except:
            print("Could not index to ES: ", sys.exc_info()[0])


        time.sleep(statsInterval)

finally:
    ledPwm.stop()
    GPIO.cleanup()
