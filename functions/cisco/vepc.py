#!/usr/bin/env python3
import paramiko
import subprocess
import datetime
from paramiko_expect import SSHClientInteraction

from functions.git import GIT_PATH
from functions.variables import TMP_PATH, DATE, TODAY, INDENT, LICENSE_EXTENSION, COMPARE_CONFIG_IGNORE, COMPARE_CONFIG_REPLACE, COMPARE_CONFIG_ADD

# Path to SFTP folder on remote host
SFTP_PATH = '/sftp/'
# Command that shows license information
SHOW_LICENSE_INFORMATION_CMD = 'show license information'

def save_config(hostname, ip, username, password):
	"""
	Function that downloads current config of Cisco vEPC node
	
	Args:
		hostname: 	node's hostname
		ip:			node's management ip address
		username:	user's login to node
		password:	user's passowrd to node
	
	Returns:
		name of the configuraiton file or log with connection error
	"""

	PROMPT = '.*{}#.*'.format(hostname)
	PROMPT_CFG = '.*{}\(config\)#.*'.format(hostname)

	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, password=password, timeout=30)
		interact = SSHClientInteraction(ssh, timeout=60, display=False)
		interact.expect(PROMPT)
		# Check node software version
		interact.send('show version')
		interact.expect(PROMPT)
		version = interact.current_output_clean.split('\n')
		# Put node version into file name
		for line in version:
			if ('Image Version:') in line:
				file_name = '{}_{}.cfg'.format(hostname, line.split()[2])
		# Save node config in path /sftp/<file_name>
		interact.send('save configuration {}{}'.format(SFTP_PATH, file_name))
		interact.expect(PROMPT)
		# Open SFTP conneciton to download config file
		sftp = ssh.open_sftp()
		sftp.get(SFTP_PATH + file_name, TMP_PATH + file_name)
		sftp.close()
		# Delete config file to free up space
		interact.send('delete {}{}'.format(SFTP_PATH, file_name))
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
	Funciton that compare given config file with one stored in git repo.
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
		# Compare configs and ommits lines with hashed password - flag "-I +B"
		# Everytime a config file is genereated the hash differs which is not relevant for config changes
		diff_results = subprocess.run(['diff', '-u', '-I', '+B', new_config, old_config_path + old_config_name], stdout=subprocess.PIPE)
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
	"""
	Function that checks license expire date and add returns license file
	if expire date is less than 30 days that will be attached notification
	mail to the user. It also add table to HTML body of the expired node for
	later email message to user

	Args:
		hostname:	node's hostname
		license:	node's license output in utf-8 format

	Returns:
		name of the license file
	"""
	for line in license.splitlines():
		if 'Expire' in line:
			expire = line.split()
			expire_string = expire[3] + expire[2] + expire[6]
			expire_date = datetime.datetime.strptime(expire_string, '%d%B%Y').date()
			if expire_date - TODAY <= datetime.timedelta(days=30):
				license_name = hostname + LICENSE_EXTENSION
				# Save current node license to file
				with open(TMP_PATH + license_name, 'w+') as f:
					f.write(license)
				# Add node license info to HTML formatted table which will be attached to mail
				with open(TMP_PATH + 'body_table.txt', 'a+') as f:
					text = '<tr><td>{}</td><td>{}</td><td>{}</td></tr>'.format(hostname, expire_date, expire_date - TODAY)
					f.write(text)

				return license_name