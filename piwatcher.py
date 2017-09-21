import RPi.GPIO as GPIO ## Import GPIO library
import time

GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
GPIO.setup(11, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
GPIO.output(11,False) ## Turn on GPIO pin 7

GPIO.setup(5, GPIO.IN) # Switch

try:
    while True:
        state = GPIO.input(5)
#        print ("State " + str(state))
        GPIO.output(11, state)
        time.sleep(0.1)

finally:
    GPIO.cleanup()