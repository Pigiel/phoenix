#!/usr/bin/env python3
import datetime

TMP_PATH = '/tmp/' # Path to folder where temporary files are stored

# Sets the current date for git commit
DATE = datetime.datetime.now().strftime('%Y-%m-%d')
# Sets today's date for time related functions e.g. license evaluaiton
TODAY = datetime.date.today()
# Indent for CLI logs
INDENT = '   '

# Messages for config comparison
COMPARE_CONFIG_IGNORE = INDENT + 'Ignoring - same config in git repo'
COMPARE_CONFIG_REPLACE = INDENT + 'Replicing file - different config found in git repo'
COMPARE_CONFIG_ADD = INDENT + 'Adding file - no config present in git repo'

# Login credentials
# 	should be kept as secrets
USERNAME = 'kubebot'
PASSWORD = 'CHANGE_ME'

# License file extension
LICENSE_EXTENSION = '.txt'

switches = {
	'SWITCH_1' : '192.168.0.10',
	'SWITCH_2' : '192.168.0.12',
}

vepcs = {
	'vEPC-1' : '192.168.0.20',
	'vEPC-2' : '192.168.0.22',
}

dns = {
	'DNS' : '192.168.0.240'
}