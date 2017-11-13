 
import spidev
import time
import os
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
def ReadChannel(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data / 1024


measuringInterval = 0.000150 # 150µs to take a value
hZ = 50
wave = 1 / hZ
# maxVals = (100 * wave) / measuringInterval
# maxVals = 1 / measuringInterval
maxVals = 5000

vcc = 5.0
vac = 220
r = 663
nbRolls = 2000

print ("Expected maxVals=" + str(maxVals))

while True:
    vals = []

    start = datetime.now()    
    idx = 0
    while idx < maxVals:
        val = ReadChannel(0)
        vals.append(val)
        idx = idx + 1
    end = datetime.now()
    delta = end - start
    print("Nb vals=" + str(len(vals)) + ", taken in " + str(delta.microseconds) + " => " + str(delta.microseconds / len(vals)) + " µs per val")
        
#    if len(vals) > maxVals:
#        vals = vals[len(vals) - maxVals:len(vals) - 1]
    gap = max(vals) - min(vals) 
    print("Channel 0:" + ", min=" + str(min(vals)) + ", max=" + str(max(vals)) + ", gap=" + str(gap) + ", len=" + str(len(vals)))

#    with open("output.json", "wb") as f:
#        f.write(json.dumps(vals).encode())
    
#    fourier = rfft(val)
#    print("fourier : " + str(fourier))
    valsnp = np.array(vals)
    valsnp = valsnp - np.average(valsnp)
    fourier = abs(fft(valsnp))
    topIdx = np.argmax(fourier)
    freqs = fftfreq(len(valsnp), (delta.microseconds / len(vals)) / 1000000)
    print("topIdx=" + str(topIdx) + ", freq=" + str(freqs[topIdx])+", val=" + str(fourier[topIdx]))
    
    vSec = (gap * vcc) / 2
    iSec = vSec / r
    iPrim = iSec * nbRolls
    wPrim = (iPrim * vac) / sqrt(2) 
    print("=> iPrim=" + ("%.2f" % iPrim) + " A" + ", watt=" + ("%.0f" % wPrim) + "W")
    
    # 1 / 50 = 0.02 
    time.sleep(1)

