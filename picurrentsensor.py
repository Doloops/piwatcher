import spidev
import time
from scipy.fftpack import fft, fftfreq
from datetime import datetime
from math import sqrt
import numpy as np

import json
import pimodule 

class PiCurrentSensor(pimodule.PiModule):
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0, 0)

    measuringInterval = 0.000150 # 150µs to take a value
    hZ = 50
    wave = 1 / hZ
    maxVals = 2500
    
    verbose = False
    
    # Function to read SPI data from MCP3008 chip
    # Channel must be an integer 0-7
    def readChannel(self, channel):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data / 1024

    def readValues(self, channel):
        vals = []
    
        start = datetime.now()    
        idx = 0
        while idx < self.maxVals:
            val = self.readChannel(channel)
            vals.append(val)
            idx = idx + 1
        end = datetime.now()
        delta = end - start
        # print("Nb vals=" + str(len(vals)) + ", taken in " + str(delta.microseconds) + " => " + str(delta.microseconds / len(vals)) + " µs per val")
        return vals, delta

    def readFourier(self, vals, delta, measure):
        valsnp = np.array(vals)
        valsnp = valsnp - np.average(valsnp)
        fourier = abs(fft(valsnp))
        topIdx = np.argmax(fourier)
        freqs = fftfreq(len(valsnp), (delta.microseconds / len(vals)) / 1000000)
        if self.verbose:
            print("* Fourier : " + str(topIdx) + ", freq=" + str(freqs[topIdx])+", val=" + str(fourier[topIdx]))
        measure["freq"] = freqs[topIdx]
        measure["amplitude"] = fourier[topIdx]


    # maxVals = (100 * wave) / measuringInterval
    # maxVals = 1 / measuringInterval

    vcc = 5
    vac = 220
    r0 = 45.8
    nbRolls = 2000
    
    asm10_iPrim_vSec_Ratio = 300
    asm30_iPrim_vSec_Ratio = 500
    
    def readDirectChannel(self, channel, measure):
        vals, delta = self.readValues(channel)
        self.readFourier(vals, delta, measure)
        vmin=min(vals)
        vmax=max(vals)
        gap = max(vals) - min(vals)
        if self.verbose: 
            print("* Dir:" + str(channel) + " : min=" + str(vmin) + ", max=" + str(vmax) + ", gap=" + str(gap) + ", len=" + str(len(vals)))
        vSec = (gap * self.vcc) / 2
        iSec = vSec / self.r0
        iPrim = iSec * self.nbRolls
        wPrim = (iPrim * self.vac) / sqrt(2)
        if self.verbose: 
            print("* Dir:" + str(channel) + " => iPrim=" + ("%.2f" % iPrim) + " A" + ", watt=" + ("%.0f" % wPrim) + "W")
        measure["vmin"] = vmin
        measure["vmax"] = vmax
        measure["gap"] = gap
        measure["iPrim"] = iPrim
        measure["wPrim"] = wPrim
        return gap, wPrim

    def readAmplifiedChannel(self, channel, measure, asmType = "ASM30"):
        vals, delta = self.readValues(channel)
        self.readFourier(vals, delta, measure)
        vmin=min(vals)
        vmax=max(vals)
        gap = max(vals) - min(vals)
        if self.verbose: 
            print("* Amp:" + str(channel) + " : min=" + str(vmin) + ", max=" + str(vmax) + ", gap=" + str(gap) + ", len=" + str(len(vals)))
        lm324nRatio = 48
        vSec = gap / lm324nRatio
        # print("CH1 : gap=" + str(gap) + ", vSec=" + str(vSec))
        if asmType == "ASM30":
            ratio = self.asm30_iPrim_vSec_Ratio
        elif asmType == "ASM10":
            ratio = self.asm10_iPrim_vSec_Ratio
        else:
            print("asmType=" + asmType + " not supported !")
            ratio = 0
        
        iPrim = vSec * ratio
        wPrim = (iPrim * self.vac) / sqrt(2)
        if self.verbose:
            print("* Amp:" + str(channel) + " => iPrim=" + ("%.2f" % iPrim) + " A" + ", watt=" + ("%.0f" % wPrim) + "W")
        measure["vmin"] = vmin
        measure["vmax"] = vmax
        measure["gap"] = gap
        measure["iPrim"] = iPrim
        measure["wPrim"] = wPrim
        return gap, wPrim

    config = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"PiCurrentSensor")
        self.config = moduleConfig

    def update(self, measure):
        for sensor in self.config["sensors"]:
            sensorId = sensor["id"]
            name = sensor["name"]
            channel = sensor["channel"]
            sensorType = sensor["type"]
            if self.verbose:
                print("Id#" + sensorId + " : " + name + " (channel=" + str(channel) + ", type=" + sensorType + ")")
            measure[sensorId] = {}
            gap = 0
            wPrim = 0
            if sensorType == "direct":
                gap, wPrim = self.readDirectChannel(channel, measure[sensorId])
            elif sensorType == "amp":
                asmType = "ASM30"
                if "asmType" in sensor:
                    asmType = sensor["asmType"]
                gap, wPrim = self.readAmplifiedChannel(channel, measure[sensorId], asmType)
            else:
                print("! Unsupported type : " + type + " for sensorId=" + sensorId)
            print(", #" + sensorId + "=" + ("%.2f" % wPrim) + "W (" + ("%.3f" % gap) + ")", end='')            

if __name__ == "__main__":
    pics = PiCurrentSensor({})
    while True:
        print("********************" + str(datetime.now()))
        measure = {}
        print("Direct 0 : Tableau *Bas*")
        pics.readDirectChannel(0, measure)
        print("Amp 1: Tableau *Haut*")
        pics.readAmplifiedChannel(1, measure)
        print("Amp 2 : Dalles")
        pics.readAmplifiedChannel(2, measure)
        print("Amp 7 : Chauffe-eau")
        pics.readAmplifiedChannel(7, measure, "ASM10")
        print("==> " + json.dumps(measure))
        time.sleep(10)
