#!/usr/bin/env python3
import paramiko
import subprocess
import datetime

from functions.git import GIT_PATH
from functions.variables import TMP_PATH, DATE, TODAY, INDENT, LICENSE_EXTENSION

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
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, password=password, timeout=30)
		# Check node software version
		output = exec_cmd(hostname, ip, username, password, 'show version')
		version = output.split()
		# Put node version into file name
		file_name = '%s_%s.cfg' % (hostname, version[4])
		# Save node config in path /sftp/<file_name>
		output = exec_cmd(hostname, ip, username, password, 'save configuration %s%s' % (SFTP_PATH, file_name))
		# Open SFTP conneciton to download config file
		sftp = ssh.open_sftp()
		sftp.get(SFTP_PATH + file_name, TMP_PATH + file_name)
		sftp.close()
		# Delete config file to free up space
		output = exec_cmd(hostname, ip, username, password, 'delete %s%s' % (SFTP_PATH, file_name))
	
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
	Funciton that compare given vepc config file with one stored in git repo.
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

def exec_cmd(hostname, ip, username, password, command):
	"""
	Function to execiute command on given remote host and returns output

	Args:
		hostname: 	node's hostname
		ip:			node's management ip address
		username:	user's login to node
		password:	user's passowrd to node
		command:	command to execiute

	Returns:
		command output
	"""
	try:
		ssh.paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, password=password, timeout=30)
		_, output, _ = ssh.exec_command(command)
		# Wait for the command to execute - required for long command execution
		output.channel.recv_exit_status()
		cmd_output = output.read().decode('utf-8')
	
	except Exception as e:
		cmd_output = str(e)
	
	finally:
		ssh.close()

	return cmd_output

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
					text = '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (hostname, expire_date, expire_date - TODAY)
					f.write(text)

				return license_name