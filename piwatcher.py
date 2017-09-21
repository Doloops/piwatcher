import RPi.GPIO as GPIO ## Import GPIO library
import time

currentLedStatus = False
disk_name="sda"

GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
GPIO.setup(11, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
GPIO.output(11,currentLedStatus) ## Turn on GPIO pin 7

GPIO.setup(5, GPIO.IN) # Switch

lastTotalIO = 0

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


try:
    while True:
        if checkDiskActivity():
            currentLedStatus = not currentLedStatus
        else:
            currentLedStatus = True
        state = GPIO.input(5)
        print ("State " + str(state) + ", currentLedStatus=" + str(currentLedStatus))
        GPIO.output(11, currentLedStatus)
        time.sleep(0.1)

finally:
    GPIO.cleanup()