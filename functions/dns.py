#!/usr/bin/env python3
import paramiko
import subprocess

from functions.git import GIT_PATH
from functions.variables import TMP_PATH, DATE

def save_config(hostname, ip, username, password):
	"""
	Function that download Bind DNS zones configuraiton

	Args:
		hostname: 	DNS server hostname
		ip: 		DNS host's ip address
		username:	user's login to DNS host
		password:	user's password to DNS host

	Returns:
		FILE_NAME: 		DNS config file - named.conf
		zones:			list of configured zones
		private1_zones: list of configured private 1 zones
		private2_zones: list of configured private 2 zones
	"""
	SFTP_PATH = '/var/named/' # Path where Bind DNS config
	ZONES_PATH = SFTP_PATH + 'zones/' # Path to zone files
	PRIVATE_PATH = ZONES_PATH + 'private/' # Path to private zone files
	FILE_NAME = 'named.conf' # Bind DNS config file
	# Initialization of empty lists
	zones, private1_zones, private2_zones = [], []

	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		ssh.connect(ip, username=username, password=password, timeout=30)

		# Check zones configured in DNS
		_, output, _ = ssh.exec_command(f'cd {ZONES_PATH}; ls zone.*')
		zones = output.read().decode('utf-8').split()
		# Check private 1 zones configured in DNS
		_, output, _ = ssh.exec_command(f'cd {PRIVATE_PATH}priv1; ls')
		private1_zones = output.read().decode('utf-8').split()
		# Check private 2 zones configured in DNS
		_, output, _ = ssh.exec_command(f'cd {PRIVATE_PATH}priv2; ls')
		private2_zones = output.read().decode('utf-8').split()

		# Open SFTP connection to download DNS config & zone files
		sftp = ssh.open_sftp()
		# Download DNS config file
		sftp.get(SFTP_PATH + FILE_NAME, TMP_PATH + FILE_NAME)
		# Download zone files
		for zone_file in zones:
			sftp.get(ZONES_PATH + zone_file, TMP_PATH + zone_file)
		# Download private 1 zones
		for zone_file in private1_zones:
			sftp.get(PRIVATE_PATH + 'priv1/' + zone_file, TMP_PATH + zone_file)
		# Download private 1 zones
		for zone_file in private2_zones:
			sftp.get(PRIVATE_PATH + 'priv2/' + zone_file, TMP_PATH + zone_file)

		# Close SFTP connection
		sftp.close()

	except Exception as e:
		# Any exception is logged to file with current date
		FILE_NAME = f'{hostname}-errors.log'
		log = DATE + ' : ' + str(e)
		with open(GIT_PATH + hostname + '/' + FILE_NAME, 'a') as f:
			f.write(log + '\n')

	finally:
		ssh.close()

	return (FILE_NAME, zones, private1_zones, private2_zones)

def files_set(new_file_list, old_file_list, file_path, file_archive_path, file_tmp_path='/tmp/'):
	"""
	Function that gets two list of files to compare their content.

	Args:
		new_file_list:		list of files to compare
		old_file_list:		list of files stored in git repo
		file_path: 			path to old files stored in git repo
		file_archive_path:	path to archive folder in git repo
		file_tmp_path: 		path to temporary folder where configs are downloaded (default /tmp)

	Retruns:
		None
	"""
	# Find same files in two lists
	files_to_compare = set(new_file_list) & set(old_file_list)
	# Find new files configured on DNS host (e.g. new zones on DNS)
	files_to_add = set(new_file_list) - set(old_file_list)
	# Find files stored in git repo and not configured on DNS anymore (e.g. zones deleted from DNS)
	files_to_archive = set(old_file_list) - set(new_file_list)

	compare_files(files_to_compare, file_path, file_tmp_path)
	add_files(files_to_add, file_path, file_tmp_path)
	archive_files(files_to_archive, file_path, file_archive_path)

def compare_files(file_list, file_path, file_tmp_path):
	"""
	Function that compares list of files with ones stored in git repository.
	If any file differs it is moved to repository for later upload.

	Args:
		file_list:		list of files to compare
		file_path: 		path to git repo files
		file_tmp_path: 	path to temporary folder where files from file_list are located

	Returns:
		None
	"""
	for file in file_list:
		diff_results = subprocess.run(['diff', '-u', file_path + file, file_tmp_path + file], stdout=subprocess.PIPE)
		if diff_results.returncode == 0:
			subprocess.run(['rm', file_tmp_path + file], stdout=subprocess.PIPE)
		else:
			subprocess.run(['mv', file_tmp_path + file, file_path], stdout=subprocess.PIPE)

def add_files(file_list, file_path, file_tmp_path):
	"""
	Function that add files from the list to git repository.

	Args:
		file_list:		list of files to add
		file_path: 		path to git repo files
		file_tmp_path: 	path to temporary folder where files from file_list are located

	Returns:
		None
	"""
	for file in file_list:
		subprocess.run(['mv', file_tmp_path + file, file_path], stdout=subprocess.PIPE)

def archive_files(file_list, file_path, file_archive_path):
	"""
	Function that archive files in git repository which are no longer configured in DNS.

	Args:
		file_list:			list of files to archive
		file_path: 			path to git repo files
		file_archive_path: 	path to archive folder in git repo

	Returns:
		None
	"""
	for file in file_list:
		subprocess.run(['mv', file_path + file, file_archive_path], stdout=subprocess.PIPE)