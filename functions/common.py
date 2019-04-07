#!/usr/bin/env python3
import os
import glob
import paramiko

import functions.cisco.switch as switch
import functions.cisco.vepc as vepc
import functions.dns as dns
from functions.git import GIT_PATH
from functions.variables import TMP_PATH, INDENT


def get_latest_config(hostname):
	"""
	Function to find the newest configuration file for the
	given hostname in git repository

	Args:
		hostname: hostname

	Returns:
		newest configuration file if available otherwise None
	"""
	config_list = sorted(os.listdir(GIT_PATH + hostname))
	if len(config_list) < 1:
		return None
	else:
		return config_list[-1]


def get_files_list(files_path, pattern='*'):
	"""
	Function to retrieve list of files in given path.
	Similar to unix command: ls <path> <file_name>*

	Args:
		files_path: path to files 
		pattern: 	pattern for search if any
					default '*'

	Returns:
		list of files in path which matches pattern
	"""
	os.chdir(files_path)
	return glob.glob(pattern)

def config_backup(node_type, hosts, username, password):
	"""
	Function that iterates through given hosts for configuration backup.
	The downloaded config is compared with one stored in git repository 
	and any files that differ are updated to repository

	Args:
		node_type:	distinguishing functions for different node types
		hosts: 		dictionary of the nodes containing HOSTNAME:IP_ADDR
		username:	user's login to host
		password:	user's password to host

	Returns:
		None
	"""
	for hostname, ip in hosts.items():
		print('Backup of host config: ' + hostname)
		# Path where host's configuraiton files are stored from git repo 
		path = GIT_PATH + hostname
		# Creates host directory if not in repo yet
		if not os.path.exists(path):
			os.mkdir(path, 0o755) # Creates folder with appropriate permissions
		old_config = get_latest_config(hostname)
		new_config = node_type.save_config(hostname, ip, username, password)
		while not new_config:
			pass # Wait till configuration file is downloaded from the node
		print(INDENT + 'Downloaded file: ' + new_config)
		if (new_config != '%s-errors.log' % hostname):
			node_type.compare_configs(hostname, new_config, old_config)
		else:
			print(INDENT + 'ERROR Configuration backup unsuccessfull. Check log file for more details')

def dns_backup(node_type, hosts, username, password):
	"""
	Function that iterates through given Bind DNS hosts for configuration backup.
	The downloaded config is compared with one stored in git repository 
	and any files that differ are updated to repository

	Args:
		node_type:	distinguishing functions for different node types
		hosts: 		dictionary of the nodes containing HOSTNAME:IP_ADDR
		username:	user's login to DNS host
		password:	user's password to DNS host

	Returns:
		None
	"""
	for hostname, ip in hosts.items():
		print('Backup of DNS host config: ' + hostname)
		# Path where host's configuraiton files are stored from git repo 
		path = GIT_PATH + hostname
		# Path to zone files in git repo
		zone_path = path + '/zones/'
		archive_path = zone_path + '/archive/'
		private_path = zone_path + '/private/'
		# Create host directory if not in repo yet
		if not os.path.exists(path):
			os.mkdir(path, 0o755) # Creates folder with appropriate permissions
		# Create zones directory if not in repo yet
		if not os.path.exists(zone_path):
			os.mkdir(zone_path, 0o755)
		# Create private zones directory if not in repo yet
		if not os.path.exists(private_path):
			os.mkdir(private_path, 0o755)
		# Create private zone 1 directroy if not in repo yet
		if not os.path.exists(private_path + 'Priv1'):
			os.mkdir(private_path + 'Priv1', 0o755)
		# Create private zone 2 directroy if not in repo yet
		if not os.path.exists(private_path + 'Priv2'):
			os.mkdir(private_path + 'Priv2', 0o755)
		# Create private zones archive directory if not in repo yet
		if not os.path.exists(archive_path):
			os.mkdir(archive_path, 0o755)
		# Create private zone 1 archive directroy if not in repo yet
		if not os.path.exists(archive_path + 'Priv1'):
			os.mkdir(archive_path + 'Priv1', 0o755)
		# Create private zone 2 archive directroy if not in repo yet
		if not os.path.exists(archive_path + 'Priv2'):
			os.mkdir(archive_path + 'Priv2', 0o755)
		# Get lists of current configuraiton files in git repos
		old_config = path + '/named.conf'
		old_zones = get_files_list(zone_path, 'zone.*')
		old_priv1 = get_files_list(private_path + 'Priv1')
		old_priv2 = get_files_list(private_path + 'Priv2')

		new_config, new_zones, new_priv1, new_priv2 = node_type.save_config(hostname, ip, username, password)

		while not new_config and new_zones and new_priv1 and new_priv2:
			pass # wait till all files are downloaded from the host

		print(INDENT + 'Downloaded file: ' + new_config)

		# Compare config files if no errors occured during download 
		if (new_config != '%s-errors.log' % hostname):
			# Compare main named.conf config file
			node_type.compare_configs(hostname, new_config, old_config)
			# Compare zones configuraiotn file
			# Note: This depends highly on config files directory structure
			node_type.files_set(new_zones, old_zones, zone_path, archive_path)
			node_type.files_set(new_priv1, old_priv1, private_path + 'Priv1', archive_path + 'Priv1')
			node_type.files_set(new_priv2, old_priv2, private_path + 'Priv2', archive_path + 'Priv2')

def expired_licenses(node_type, hosts, username, password):
	"""
	Function that iterates through given hosts to validate license.
	
	Args:
		node_type:	distinguishing functions for different node types
		hosts: 		dictionary of the nodes containing HOSTNAME:IP_ADDR
		username:	user's login to host
		password:	user's password to host

	Returns:
		list of licenses to expire
	"""
	licenses = []
	for hostname, ip in hosts.items():
		print('Checking license of ' + hostname)
		# Get current license info from the node
		license = exec_cmd(hostname, ip, username, password, node_type.SHOW_LICENSE_INFORMATION_CMD)
		# Check if license download is successful
		if license != None:
			# Validate node license - if expire date is near then returns license file
			license_file = node_type.validate_license(hostname, license)
			# Add license to list of expired licences
			if license_file != None:
				licenses.append(license_file)

def clear_temporary_files(files_extension):
	"""
	Function to remove files temporary created by this script

	Args:
		files_extension: files extension to delete from TMP_PATH

	Returns:
		None
	"""
	os.system('rm ' + TMP_PATH + '*' + files_extension)