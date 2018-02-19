import spidev
import time
from scipy.fftpack import fft, fftfreq
from datetime import datetime
from math import sqrt
from statistics import mean
import numpy as np

import json
from piwatcher import pimodule 

import matplotlib.pyplot as plt
        
class PiCurrentSensor (pimodule.PiModule):
    # Open SPI bus
    spi = spidev.SpiDev()
    spi.open(0, 0)

# 125.0 MHz	125000000
#  62.5 MHz	 62500000
#  31.2 MHz  31200000
#  15.6 MHz  15600000
#   7.8 MHz   7800000
#   3.9 MHz   3900000
#  1953 kHz   1953000
#   976 kHz    976000
#   488 kHz    488000
#   244 kHz    244000
#   122 kHz    122000
#    61 kHz     61000
#  30.5 kHz     30500
#  15.2 kHz     15200
#  7629 Hz       7629
    
    spi.max_speed_hz = 7800000 # 488000 # 15600000 # 

    signalHz = 50
    nbWaves = 5
    nbVals = 100
    nbPointsPerWave = nbVals / nbWaves
    timingForAllWaves = (nbWaves / signalHz) 
    timingBetweenPoints = timingForAllWaves / nbVals
    shouldTake = timingBetweenPoints * nbVals
    
    print("nbWaves=" + str(nbWaves) + ", nbPointsPerWave=" + str(nbPointsPerWave) + ", timingForAllWaves=" + str(timingForAllWaves)
        + ", timingBetweenPoints=" + str(timingBetweenPoints) + ", shoudTake=" + str(shouldTake))
    
    verbose = True
    dumpVals = True
    plotVals = False
    
    config = None

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"PiCurrentSensor")
        self.config = moduleConfig
        if self.plotVals:
            plt.ion()
    
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


    def readAllValues(self, channels):
        # Perform a cold start
        for j in range(0, 20):
            for channel in channels:
                self.readChannel(channel)
        
        vals = [0] * (max(channels) + 1)
        for i in channels:
            vals[i] = [0] * self.nbVals
        timings = [0] * self.nbVals
        start = datetime.now()
        last = start
        totalSleep = 0
        totalTook = 0
        for j in range(self.nbVals):
            mnow = datetime.now() - start
            timings[j] = mnow.microseconds
            for channel in channels:
                vals[channel][j] = self.readChannel(channel)
            took = datetime.now() - last
            sleepTime = max(self.timingBetweenPoints - (took.microseconds / 1000000), 0)
            totalSleep = totalSleep + (sleepTime * 1000000)
            totalTook = totalTook + took.microseconds
#            print("Took : " + ("%.10f" % took.microseconds) + ", sleep=" + ("%.10f" % sleepTime))
            if sleepTime > 0:
                time.sleep(sleepTime)
            last = datetime.now()
        end = datetime.now()
        delta = end - start
        print("totalSleep=" + str(totalSleep) + ", totalTook=" + str(totalTook) 
                + ", delta=" + str(delta.microseconds) + ", shouldTake=" + str(self.shouldTake))
        print("* vals taken in " + str(delta.microseconds) + "µs "
             + "(" + ("%.2f" % (1000000/delta.microseconds)) + " Hz) => "
             + str(delta.microseconds / len(vals)) + " µs per val")
        return vals, timings, delta

    vcc = 5
    vac = 220
    lm324nRatio = 24
    asm10_iPrim_vSec_Ratio = 300
    asm30_iPrim_vSec_Ratio = 500
    sct013_iPrim_vSec_Ratio = 826
    
    noiseOffset = 0
    
    def computeChannel(self, channel, measure, asmType, channelValues, noiseValues, timings, delta, threshold):
        if self.plotVals and channel == 4:
            plt.plot(channelValues)
        vals = channelValues - noiseValues
        if self.plotVals and channel == 4:
            plt.plot(vals, label="After")
        freq, amplitude = self.readFourier(vals, delta, measure)
        vmean0 = mean(vals)
        valps = abs(np.array(vals)-vmean0)
        vmean = mean(valps)
        realgap = vmean * (np.pi / 2)
        vSec = (realgap * self.vcc) / self.lm324nRatio
        if self.verbose:
            print("* vmean0=" + str(vmean0) + ", vmean=" + str(vmean) + ", min=" + str(min(vals)) + ", max=" + str(max(vals)))
        if asmType == "ASM30":
            ratio = self.asm30_iPrim_vSec_Ratio
        elif asmType == "ASM10":
            ratio = self.asm10_iPrim_vSec_Ratio
        elif asmType == "SCT013":
            ratio = self.sct013_iPrim_vSec_Ratio
        else:
            print("asmType=" + asmType + " not supported !")
            ratio = 0

        iPrim = vSec * ratio
        wPrim = (iPrim * self.vac) / sqrt(2)
        if self.verbose:
            print("* Amp:" + str(channel) + " => iPrim=" + ("%.2f" % iPrim) + " A" + ", watt=" + ("%.0f" % wPrim) + "W")
        if wPrim < threshold:
            wPrim = 0
        measure["iPrim"] = iPrim
        measure["wPrim"] = wPrim
        measure["vmean"] = vmean
        return wPrim, freq, amplitude, vmean, iPrim
        
        
    def update(self, measure):
        print (", Current Sensors :")
        allChannels = range(0, 8)
        
        for tries in range(0,10):
            vals, timings, delta = self.readAllValues(allChannels)
            noiseChannel = self.config["noise.channel"]
            npNoise = np.array(vals[noiseChannel])
            noiseGap = max(npNoise) - min(npNoise)
            print("=> Noise level " + str(noiseGap))
            if noiseGap < 0.0075:
                break
        measure["noiseLevel"] = noiseGap
        
        if self.dumpVals:
            for channel in allChannels:
                with open("/run/user/1000/output-" + str(channel) + ".json", "wb") as f:
                    f.write(json.dumps(vals[channel]).encode())
                            
        if self.plotVals:
            plt.clf()
            plt.axis([0, self.nbVals, -1, 1]) 
            plt.plot(vals[noiseChannel], label="Noise")
        for sensor in self.config["sensors"]:
            sensorId = sensor["id"]
            name = sensor["name"]
            channel = sensor["channel"]
            sensorType = sensor["type"]
            if self.verbose:
                print("*** Id#" + sensorId + " : " + name + " (channel=" + str(channel) + ", type=" + sensorType + ")")
                
            measure[sensorId] = {}
            asmType = "ASM30"
            if "asmType" in sensor:
                asmType = sensor["asmType"]
            threshold = 0
            if "threshold" in sensor:
                threshold = sensor["threshold"]

#                wPrim, freq, amplitude, vmean = self.readAmplifiedChannel(channel, measure[sensorId], asmType)
            wPrim, freq, amplitude, vmean, iPrim = self.computeChannel(channel, measure[sensorId], asmType, 
                np.array(vals[channel]), npNoise, timings, delta, threshold)

            if wPrim == 0:
                print ("=> #" + sensorId + "=OFF")
            else:
                print("=> #" + sensorId + "=\t" + ("%.2f" % wPrim) + "W"
                      + " \t(" + ("%.2f" % freq) + "Hz, " + ("%.2f" % amplitude)
                      + ", vmean=" + ("%.6f" % vmean) + ")")
        if self.plotVals:
            plt.pause(30)

if __name__ == "__main__":
    pics = PiCurrentSensor({})
    while True:
        print("********************" + str(datetime.now()))
        measure = {}
        print("Direct 0 : Tableau *Bas*")
        pics.readAmplifiedChannel(0, measure)

        print("Amp 1: Tableau *Haut*")
        pics.readAmplifiedChannel(5, measure)

        print("Amp 2 : Chauffe-eau")
        pics.readAmplifiedChannel(2, measure, "ASM10")

        print("Amp 3 : Chauffage Living")
        pics.readAmplifiedChannel(3, measure)

        print("Amp 4 : TV Living")
        pics.readAmplifiedChannel(4, measure, "ASM10")

        print("Amp 7 : Dalles")
        pics.readAmplifiedChannel(7, measure)

        time.sleep(2)
        continue

        print("==> " + json.dumps(measure))

        time.sleep(10)
