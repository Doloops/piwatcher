import spidev

import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft, fftfreq
from datetime import datetime
import time
import json
import socket

class CurrentSensorPlotter:

    doPlot = False
    doSocket = True
    host = "192.168.1.105"
    port = 1088

    spi = spidev.SpiDev()
    spi.open(0, 0)

# 125.0 MHz     125000000
#  62.5 MHz      62500000
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

    spi.max_speed_hz =  7800000 # 1953000 # 3900000 # 1953000 # 15600000 # 488000 # 15600000 # 
    spi.max_speed_hz = 61000
    spi.max_speed_hz =  7800000
    nbVals = 250
    verbose = True
    signalHz = 50
    nbWaves = 2
    nbPointsPerWave = nbVals / nbWaves
    timingForAllWaves = (nbWaves / signalHz) 
    timingBetweenPoints = timingForAllWaves / nbVals
    print ("timingBetweenPoints=" + str(timingBetweenPoints))

    def __init__(self):
        if self.doPlot:
            plt.ion()
        if self.doSocket:
            self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sk.connect((self.host, self.port))
            print ("Connecting to {}:{}".format(self.host,self.port))
            self.skmf = self.sk.makefile(mode="w")


    def readFourier(self, vals, timings, delta):
        valsnp = np.array(vals)
        valsnp = valsnp - np.average(valsnp)
        fourier = abs(fft(valsnp))
        topIdx = np.argmax(fourier)
        freqs = fftfreq(len(valsnp), (delta.microseconds / len(vals)) / 1000000)
        if self.verbose:
            print("* Fourier : " + str(topIdx) + ", freq=" + str(freqs[topIdx])+", val=" + str(fourier[topIdx]))
#        plt.plot(fourier)
        return freqs[topIdx], fourier[topIdx]

    def readChannel(self, channel):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data / 1024

    def readValues(self, channels):
#        vals = [[0] * self.nbVals] * len(channels)
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
        print("totalSleep=" + str(totalSleep) + ", totalTook=" + str(totalTook))
        print("* vals taken in " + str(delta.microseconds) + "µs "
             + "(" + ("%.2f" % (1000000/delta.microseconds)) + " Hz) => "
             + str(delta.microseconds / len(vals)) + " µs per val")
        return vals, timings, delta

    def loop(self):
        while True:
            if self.doPlot:
                plt.clf()
                plt.axis([0, self.nbVals, -1, 1])
#            plt.axis([0, 100000, 0, 1])
#            plt.axis([0, 20, 0, 200])
            channels = range(0,8) #range(4, 8)
            vals, timings, delta = self.readValues(channels)
#            noise = np.array(vals[0])
            for channel in channels:
                print ("Display Ch#" + str(channel) + ", min=" + str(min(vals[channel])) + ", max=" + str(max(vals[channel])))
#                self.readFourier(vals[channel], timings, delta)
                if self.doPlot:
                    plt.plot(np.array(vals[channel]), label=('Ch#' + str(channel)))
            if self.doSocket:
#                self.sk.send(bytearray(json.dumps(vals[channel]) + "\n","utf-8"))
                self.skmf.write(json.dumps(vals) + "\n")
                self.skmf.flush()
                time.sleep(0.1)
#                plt.scatter(timings, vals[channel], marker='.', linewidths=1)
            if self.doPlot:
                plt.pause(0.1)

if __name__ == "__main__":
    plotter = CurrentSensorPlotter()
    plotter.loop()
