#1/usr/bin/env python

from uuid import getnode

def get_mac():
    mac = getnode()
    serial = ''.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
    return serial

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
