import pimodule
import re
import subprocess

class CpuWatcher(pimodule.PiModule):
    cpuTempPattern = re.compile("temp=(.*)'C")

    def __init__(self):
        pimodule.PiModule.__init__(self,"CPU")

    def getCPUTemp(self):
        result = subprocess.check_output(["/opt/vc/bin/vcgencmd", "measure_temp"], shell=False).decode("utf-8")
        match = self.cpuTempPattern.match(result)
        temp = float(match.group(1))
        return temp    

    def getCPULoad(self):
        try:
            loadavg_file = open("/proc/loadavg")
            line = loadavg_file.read().strip().split()
            cpuLoad = float(line[0])
            return cpuLoad
        finally:
            loadavg_file.close()

    def update(self, measure):
        measure["cpuTemp"] = self.getCPUTemp()
        measure["cpuLoad"] = self.getCPULoad()
        cpuMessage = ", cpuTemp=" + ("%2.1f'C" % measure["cpuTemp"]) + ", load=" + ("%.2f" % measure["cpuLoad"])
        print(cpuMessage, end='')

    def shutdown(self):
        print("Shutdown " + self.getModuleName())

