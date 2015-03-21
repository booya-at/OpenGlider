import os
import json

with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')) as __configfile:
    config = json.load(__configfile)