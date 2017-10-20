import RPi.GPIO as GPIO ## Import GPIO library
import time
import sys
import select

# States
# 0 : Confort
# 1 : (MN) Arrêt
# 2 : (MP) Hors-gel
# 3 : Eco

PIN_MP=16
PIN_MN=18

state = 0

GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
GPIO.setup(PIN_MP, GPIO.OUT)
GPIO.output(PIN_MP,False)
GPIO.setup(PIN_MN,GPIO.OUT)
GPIO.output(PIN_MN,False)

def setState(state):
        print ("State " + str(state))
        if state == 0:
            GPIO.output(PIN_MP, False)
            GPIO.output(PIN_MN, False)
        elif state == 1:
            GPIO.output(PIN_MP, False)
            GPIO.output(PIN_MN, True)
        elif state == 2:
            GPIO.output(PIN_MP, True)
            GPIO.output(PIN_MN, False)
        elif state == 3:
            GPIO.output(PIN_MP, True)
            GPIO.output(PIN_MN, True)


try:
    while True:
        input = sys.stdin.readline()
        print("Read : " + input)
        try:
            state = int(input)
            setState(state)
        except:
            print("Invalid input : " + input)

finally:
    GPIO.cleanup()

