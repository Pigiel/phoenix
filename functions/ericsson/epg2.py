#/usr/bin/env python
import paramiko
import subprocess
import datetime
from paramiko_expect import SSHClientInteraction

from functions.git import GIT_PATH
from functions.variables import TMP_PATH, DATE, TODAY, INDENT, LICENSE_EXTENSION, USERNAME, COMPARE_CONFIG_IGNORE, COMPARE_CONFIG_REPLACE, COMPARE_CONFIG_ADD

# Path to sftp folder on Ericsson node where SFTP download is enabled
SFTP_PATH = '/flash/'


def save_config(hostname, ip, username, password):
	"""
	Downloads current configuration of Ericsson EPG 2.X node
	
	Args:
		hostname: 	hostname
		ip: 		host's ip address
		username: 	user's login
		password: 	user's password
	
	Returns:
		name of the configuration file or log with connection error
	"""

	PROMPT = '.*\[local\]{}#.*'.format(hostname)
	PROMPT_CFG = '.*{}\(config\)#.*'.format(hostname)
	PROMPT_BASH = '.*bash-.*$.*'
	PROMPT_CONFIRM = '.*[yes,no].*'

	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, password=password, timeout=30)
		interact = SSHClientInteraction(ssh, timeout=60, display=SSH_DISPLAY_LOGGING)
		interact.expect(PROMPT)
		# Checking software version on the node
		interact.send('start shell')
		interact.expect(PROMPT_BASH)
		interact.send('show_epg_version |grep -v +')
		interact.expect(PROMPT_BASH)
		version = interact.current_output_clean.split('\n')
		interact.send('exit')
		interact.expect(PROMPT)
		# Puts node version into file name
		for line in version:
			if ('version') in line:
				file_name = '{}_{}.xml'.format(hostname, line.split()[4])
		# Save the node configuration
		interact.send('config')
		interact.expect(PROMPT_CFG)
		interact.send('save {}'.format(file_name))
		interact.expect([PROMPT_CFG, PROMPT_CONFIRM])
		if interact.last_match == PROMPT_CONFIRM:
			interact.send('yes')
			interact.expect(PROMPT_CFG)
		interact.send('exit')
		interact.expect(PROMPT)
		# Open SFTP conneciton to download saved config file
		sftp = ssh.open_sftp()
		sftp.get(SFTP_PATH + file_name, TMP_PATH + file_name)
		sftp.close()
		# Delete the configuration file to free up space
		interact.send('delete {}'.format(file_name))
		interact.expect([PROMPT, PROMPT_CONFIRM])
		if interact.last_match == PROMPT_CONFIRM:
			interact.send('y')
			interact.expect(PROMPT)
	except Exception as e:
		# Any exception is logged to file with current date
		file_name = '{}-errors.log'.format(hostname)
		log = DATE + ' : ' + str(e)
		with open(GIT_PATH + hostname + '/' + file_name, 'a') as f:
			f.write(log + '\n')		
	finally:
		ssh.close()
	return file_name

def compare_configs(hostname, config_name, old_config_name):
	"""
	Compares configuration file downloaded from the node with one stored in SSC EPC
	gitlab repository. Configuration file is uploaded to repository only if config
	differs between downloaded file and one stored in repo

	Args:
		hostname: 			hostname
		config_name: 		name of the configuration file downloaded from the node
		old_config_name: 	name of the configuration file stored in gitlab repo

	Retruns:
		None
	"""

	new_config = TMP_PATH + config_name
	old_config_path = GIT_PATH + hostname + '/'

	# If config file names are the same (e.g. sw version matches) then compare configs
	if (config_name == old_config_name):
		# Compare configs "-I +" flag ommits lines with hashed passwords (e.g. user passwords)
		# Everytime a config file is generated the hash differs and it's not relevant for config changes 
		diff_results = subprocess.run(['diff', '-u', '-I', '!', '-I', '+', new_config, old_config_path + old_config_name], stdout=subprocess.PIPE)
		if diff_results.returncode == 0:
			# If configs are the same then remove downloaded config file
			print(COMPARE_CONFIG_IGNORE)
			subprocess.run(['rm', new_config], stdout=subprocess.PIPE)
		else:
			# If configs differs then move downloaded file to git repo
			print(COMPARE_CONFIG_REPLACE)
			subprocess.run(['mv', new_config, old_config_path], stdout=subprocess.PIPE)
	# If config file names differs (e.g. different SW version) then move downloaded file to git repo
	else:
		print(COMPARE_CONFIG_ADD)
		subprocess.run(['mv', new_config, old_config_path], stdout=subprocess.PIPE)

def validate_license(hostname, license):
	pass