#!/usr/bin/env python3
import paramiko
import subprocess
from paramiko_expect import SSHClientInteraction

from functions.git import GIT_PATH
from functions.variables import TMP_PATH, DATE, INDENT

def save_config(hostname, ip, username, password):
	"""
	Function that downloads running-configuration from Cisco switch
	Args:
		hostname: 	switch hostname
		ip:			switch management ip address
		username:	user's login switch
		password:	user's passowrd to switch
	
	Returns:
		name of the configuraiton file or log with connection error
	"""
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, password=password,
			timeout=30,	look_for_keys=False, allow_agent=False)
		# Library to interact with with SSH output
		interact = SSHClientInteraction(ssh, timeout=30, display=False)
		# Wait for switch prompt user (.*>) or privileged (.*#)
		interact.expect([hostname +'>', hostname +'#'])
		# If user mode enable privileged
		if interact.last_match == hostname +'>':
			interact.send('enable')
			interact.expect('Password: ')
			interact.send(password)
			interact.expect(hostname + '#') # Wait for privilage mode
		file_name = hostname + '.cfg'
		# Set terminal length for session to infinite
		# (no "-- More --" prompt)
		interact.send('terminal length 0')
		interact.expect(hostname + '#')
		interact.send('show running-config')
		interact.expect(hostname + '#')
		config = interact.current_output_clean
		with open(TMP_PATH + file_name, 'a') as f:
			f.write(config)
	
	except Exception as e:
		# Any exception is logged to file with current date
		file_name = '%s-errors.log' % hostname
		log = DATE + ' : ' + str(e)
		with open(GIT_PATH + hostname + '/' + FILE_NAME, 'a') as f:
			f.write(log + '\n')
	
	finally:
		ssh.close()

	return file_name

def compare_configs(hostname, config_name, old_config_name):
	"""
	Funciton that compare given DNS config file with one stored in git repo.
	If configs differs then new one is moved to repo path

	Args:
		hostname:		 device hostname
		config_name:	 config file name downloaded from the node
		old_config_name: config file name stored in git repo
	
	Return:
		None
	"""
	new_config = TMP_PATH + config_name
	old_config_path = GIT_PATH + hostname + '/'
	# If config file names are the same (e.g. same SW version) then compare configs
	if (config_name == old_config_name):
		# Compare configs and ommits lines with hashed password - flag "-I +"
		# Everytime a config file is genereated the hash differs which is not relevant for config changes
		diff_results = subprocess.run(['diff', '-u', '-I', '+', new_config, old_config_path + old_config_name], stdout=subprocess.PIPE)
		if diff_results.returncode == 0:
			# If configs are the same then remove downloaded config file
			print(INDENT + 'Ignoring - same config in git repo')
			subprocess.run(['rm', new_config], stdout=subprocess.PIPE)
		else:
			# If configs differs then move downloaded file to git repo
			print(INDENT + 'Replicing file - different config found in git repo')
			subprocess.run(['mv', new_config, old_config_path], stdout=subprocess.PIPE)
	# If config file names differs (e.g. different SW version) then move downloaded file to git repo
	else:
		print(INDENT + 'Adding file - no config present in git repo')
		subprocess.run(['mv', new_config, old_config_path], stdout=subprocess.PIPE)