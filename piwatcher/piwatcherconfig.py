import json
from os.path import expanduser

def getPiWatcherConfig():
    with (open(expanduser("~") + "/.piwatcher/config.json")) as confFile:
        confString = confFile.read()
        pwConfig = json.loads(confString)
        print ("Start with config : " + str(pwConfig))
        return pwConfig


