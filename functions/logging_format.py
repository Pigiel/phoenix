#!/usr/bin/env python3
import logging

# Switch for log verbosity by the script
LOGGING_INFO = 'debug'
#LOGGING_INFO = 'info'

# Format of logging messages for the script
if (LOGGING_INFO == 'debug'):
	logging.basicConfig(format='[%(levelname)s] %(asctime)s : %(message)s', level=logging.DEBUG)
	SSH_DISPLAY_LOGGING = True
else:
	logging.basicConfig(format='[%(levelname)s] %(asctime)s : %(message)s', level=logging.INFO)
	SSH_DISPLAY_LOGGING = False