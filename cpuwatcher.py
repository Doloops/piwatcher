import re
import subprocess

class CpuWatcher:
    cpuTempPattern = re.compile("temp=(.*)'C")


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
        cpuMessage = ", cpuTemp=" + str(measure["cpuTemp"]) + ", load=" + str(measure["cpuLoad"])
        print(cpuMessage, end='')

