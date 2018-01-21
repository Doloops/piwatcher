from piwatcher import pimodule
import re
import subprocess
import time

class CpuWatcher(pimodule.PiModule):
    cpuTempPattern = re.compile("temp=(.*)'C")
    cpuTempFile = "/sys/devices/virtual/thermal/thermal_zone0/temp"

    def __init__(self, moduleConfig):
        pimodule.PiModule.__init__(self,"CPU")
        if "cpuTempFile" in moduleConfig:
            self.cpuTempFile = moduleConfig["cpuTempFile"]

    # Deprecated, long method
    def getCPUTemp_VCGENCMD(self):
        start = time.time()
        result = subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_temp"], shell=False).decode("utf-8")
        match = self.cpuTempPattern.match(result)
        temp = float(match.group(1))

        end = time.time()
        print("{CT:" + ("%.3f"%((end-start)*1000)) + "}", end='')

        return temp

    def getCPUTemp(self):
        with open(self.cpuTempFile) as temp_file:
            line = temp_file.read()
            temp = float(line)
            # Raspberry PI reports temp with 3 digits after the ., but BananaPI reports temps on 2 digits only.
            if temp > 1000:
                temp = temp / 1000
            return temp

    def getCPULoad(self):
        with open("/proc/loadavg") as loadavg_file:
            line = loadavg_file.read().strip().split()
            cpuLoad = float(line[0])
            return cpuLoad

    def update(self, measure):
        measure["cpuTemp"] = self.getCPUTemp()
        measure["cpuLoad"] = self.getCPULoad()
        cpuMessage = ", cpuTemp=" + ("%2.1f'C" % measure["cpuTemp"]) + ", load=" + ("%.2f" % measure["cpuLoad"])
        print(cpuMessage, end='')

    def shutdown(self):
        print("Shutdown " + self.getModuleName())

