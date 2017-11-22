import spidev
import time
from scipy.fftpack import fft, fftfreq
from datetime import datetime
from math import sqrt
from statistics import mean
import numpy as np

import json
from piwatcher import pimodule 

class PiCurrentSensor(pimodule.PiModule):
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0, 0)

    measuringInterval = 0.000150 # 150µs to take a value
    hZ = 50
    wave = 1 / hZ
    nbWaves = 10
    maxVals = nbWaves * wave / measuringInterval
    
    verbose = False
    dumpVals = True
    
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
        if self.verbose:
            print("* #vals=" + str(len(vals)) + ", taken in " + str(delta.microseconds) + "µs (" + ("%.2f" % (1000000/delta.microseconds)) + " Hz) => "
                  + str(delta.microseconds / len(vals)) + " µs per val")
        if self.dumpVals:
            with open("/run/user/1000/output-" + str(channel) + ".json", "wb") as f:
                f.write(json.dumps(vals).encode())

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
        return freqs[topIdx], fourier[topIdx]


    # maxVals = (100 * wave) / measuringInterval
    # maxVals = 1 / measuringInterval

    vcc = 5
    vac = 220
    r0 = 45.8
    nbRolls = 2000
    lm324nRatio = 48
    
    asm10_iPrim_vSec_Ratio = 300
    asm30_iPrim_vSec_Ratio = 500
    
    def computeGap(self, vals):
        vmin=min(vals)
        vmax=max(vals)
        if True:
            gap = max(vals) - min(vals)
            return gap, vmin, vmax
        else:
            sortedVals = sorted(vals)
            xtremSize = int(len(vals) / 50)
            minVals = mean(sortedVals[0:xtremSize])
            maxVals = mean(sortedVals[len(sortedVals) - xtremSize:len(sortedVals)])
            gap = maxVals - minVals
            return gap, vmin, vmax
    
    def readDirectChannel(self, channel, measure):
        vals, delta = self.readValues(channel)
        freq, amplitude = self.readFourier(vals, delta, measure)
        gap, vmin, vmax = self.computeGap(vals)
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
        return gap, wPrim, freq, amplitude

    def readAmplifiedChannel(self, channel, measure, asmType = "ASM30"):
        vals, delta = self.readValues(channel)
        freq, amplitude = self.readFourier(vals, delta, measure)
        gap, vmin, vmax = self.computeGap(vals)
        if self.verbose: 
            print("* Amp:" + str(channel) + " : min=" + str(vmin) + ", max=" + str(vmax) + ", gap=" + str(gap) + ", len=" + str(len(vals)))
        vSec = (gap * self.vcc) / self.lm324nRatio
        if self.verbose:
            print("* gap=" + str(gap) + ", vSec=" + str(vSec))
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
        return gap, wPrim, freq, amplitude

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
                gap, wPrim, freq, amplitude = self.readDirectChannel(channel, measure[sensorId])
            elif sensorType == "amp":
                asmType = "ASM30"
                if "asmType" in sensor:
                    asmType = sensor["asmType"]
                gap, wPrim, freq, amplitude = self.readAmplifiedChannel(channel, measure[sensorId], asmType)
            else:
                print("! Unsupported type : " + type + " for sensorId=" + sensorId)
            print(", #" + sensorId + "=" + ("%.2f" % wPrim) + "W (" + ("%.2f" % freq) + "Hz, " + ("%.2f" % amplitude) + ", gap=" + ("%.3f" % gap) + ")", end='')

if __name__ == "__main__":
    pics = PiCurrentSensor({})
    while True:
        print("********************" + str(datetime.now()))
        measure = {}
        print("Direct 0 : Tableau *Bas*")
        pics.readDirectChannel(0, measure)

        print("Amp 1: Tableau *Haut*")
        pics.readAmplifiedChannel(1, measure)

        print("Amp 7 : Dalles")
        pics.readAmplifiedChannel(7, measure)

        print("Amp 2 : Chauffe-eau")
        pics.readAmplifiedChannel(2, measure, "ASM10")

        time.sleep(10)
        continue

        print("==> " + json.dumps(measure))

        time.sleep(10)
