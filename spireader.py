 
import spidev
import time
from scipy.fftpack import fft, fftfreq
from datetime import datetime
from math import sqrt
import numpy as np

import json
 
# Open SPI bus
spi = spidev.SpiDev()
spi.open(0, 0)

 
# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def readChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data / 1024

measuringInterval = 0.000150 # 150µs to take a value
hZ = 50
wave = 1 / hZ
maxVals = 2500

def readValues(channel):
    vals = []

    start = datetime.now()    
    idx = 0
    while idx < maxVals:
        val = readChannel(channel)
        vals.append(val)
        idx = idx + 1
    end = datetime.now()
    delta = end - start
    # print("Nb vals=" + str(len(vals)) + ", taken in " + str(delta.microseconds) + " => " + str(delta.microseconds / len(vals)) + " µs per val")
    return vals, delta

def readFourier(vals, delta):
    valsnp = np.array(vals)
    valsnp = valsnp - np.average(valsnp)
    fourier = abs(fft(valsnp))
    topIdx = np.argmax(fourier)
    freqs = fftfreq(len(valsnp), (delta.microseconds / len(vals)) / 1000000)
    print("* Fourier : " + str(topIdx) + ", freq=" + str(freqs[topIdx])+", val=" + str(fourier[topIdx]))


# maxVals = (100 * wave) / measuringInterval
# maxVals = 1 / measuringInterval

vcc = 4.95
vac = 220
r0 = 663
nbRolls = 2000

asm30_iPrim_vSec_Ratio = 538.46
print ("Expected maxVals=" + str(maxVals))

def readDirectChannel(channel):
    vals, delta = readValues(channel)
    readFourier(vals, delta)
    vmin=min(vals)
    vmax=max(vals)
    gap = max(vals) - min(vals) 
    print("* Dir:" + str(channel) + " : min=" + str(vmin) + ", max=" + str(vmax) + ", gap=" + str(gap) + ", len=" + str(len(vals)))
    vSec = (gap * vcc) / 2
    iSec = vSec / r0
    iPrim = iSec * nbRolls
    wPrim = (iPrim * vac) / sqrt(2) 
    print("* Dir:" + str(channel) + " => iPrim=" + ("%.2f" % iPrim) + " A" + ", watt=" + ("%.0f" % wPrim) + "W")

def readAmplified(channel):
    vals, delta = readValues(channel)
    readFourier(vals, delta)
    vmin=min(vals)
    vmax=max(vals)
    gap = max(vals) - min(vals) 
    print("* Amp:" + str(channel) + " : min=" + str(vmin) + ", max=" + str(vmax) + ", gap=" + str(gap) + ", len=" + str(len(vals)))
    lm324nRatio = 48
    vSec = gap / lm324nRatio
    # print("CH1 : gap=" + str(gap) + ", vSec=" + str(vSec))
    iPrim = vSec * asm30_iPrim_vSec_Ratio
    wPrim = (iPrim * vac) / sqrt(2)
    print("* Amp:" + str(channel) + " => iPrim=" + ("%.2f" % iPrim) + " A" + ", watt=" + ("%.0f" % wPrim) + "W")

while True:
    print("********************" + str(datetime.now()))
    print("Direct 0 : Tableau *Bas*")
    readDirectChannel(0)
    print("Amp 1: Tableau *Haut*")
    readAmplified(1)
    print("Amp 2 : Dalles")
    readAmplified(2)
    print("Amp 7 : Chauffe-eau")
    readAmplified(7)
#    if len(vals) > maxVals:
#        vals = vals[len(vals) - maxVals:len(vals) - 1]
    
#    with open("output.json", "wb") as f:
#        f.write(json.dumps(vals).encode())
    
#    fourier = rfft(val)
#    print("fourier : " + str(fourier))
    
    
    
    # 1 / 50 = 0.02 
    time.sleep(10)

