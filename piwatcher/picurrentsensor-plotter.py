import spidev

import numpy as np
import matplotlib.pyplot as plt
from scipy.fftpack import fft, fftfreq
from datetime import datetime
import time

class CurrentSensorPlotter:

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1953000 # 3900000 # 1953000 # 15600000 # 488000 # 15600000 # 488000
    nbVals = 500
    verbose = True
    signalHz = 50
    nbWaves = 10
    nbPointsPerWave = nbVals / nbWaves
    timingForAllWaves = (nbWaves / signalHz) 
    timingBetweenPoints = timingForAllWaves / nbVals
    print ("timingBetweenPoints=" + str(timingBetweenPoints))
    


    def __init__(self):
        plt.ion()

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
            plt.clf()
            plt.axis([0, 100000, 0, 1])
#            plt.axis([0, 20, 0, 200])
            channels = range(0, 8)
            vals, timings, delta = self.readValues(channels)
            for channel in range(5, 6):
                self.readFourier(vals[channel], timings, delta)
#                plt.plot(vals, label=('Ch#' + str(channel)))
                print ("Display Ch#" + str(channel))
                plt.scatter(timings, vals[channel], marker='.', linewidths=1)
            plt.pause(0.1)

if __name__ == "__main__":
    plotter = CurrentSensorPlotter()
    plotter.loop()
