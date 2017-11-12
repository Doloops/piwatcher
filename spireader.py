 
import spidev
import time
import os
from datetime import datetime
 
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
maxVals = (3 * wave) / measuringInterval

print ("Expected maxVals=" + str(maxVals))

ts = 0
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
    print("Took " + str(len(vals)) + " in " + str(delta.microseconds) + " => " + str(delta.microseconds / len(vals)) + " µs per val")
        
#    if len(vals) > maxVals:
#        vals = vals[len(vals) - maxVals:len(vals) - 1]
    gap = max(vals) - min(vals) 
    print("Channel 0:" + str(val) + ",min=" + str(min(vals)) + ", max=" + str(max(vals)) + ", gap=" + str(gap) + ", len=" + str(len(vals)))
    ts= 0
    
    # 1 / 50 = 0.02 
    time.sleep(1)
