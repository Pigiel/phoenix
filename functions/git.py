#!/usr/bin/env python3
import subprocess

from functions.variables import DATE

# Path to git repository in container
GIT_PATH = '/git/config'
# Commit message
DAILY_TAG_MESSAGE = 'Configuration of lab nodes from ' + DATE

def git_set_global_settings():
	"""Set git global settings"""
	subprocess.call(['git', 'config', '--global', 'user.email', 'kube-bot@kubernetes.local'])
	subprocess.call(['git', 'config', '--global', 'user.name', 'KubeBot'])

def git_pull():
	"""Fetch files from remote repository"""
	subprocess.call(['git', '-C', GIT_PATH, 'pull'])

def git_push(follow_tags=None):
	"""Update remote repository with associated objects"""
	if (follow_tags == None):
		subprocess.run(['git', '-C', GIT_PATH, 'push'])
	else:
		subprocess.run(['git', '-C', GIT_PATH, 'push', follow_tags])

def git_add():
	"""Add all files to the commit"""
	subprocess.run(['git', '-C', GIT_PATH, 'add', '.'])

def git_commit(message=DATE):
	"""Record changes to git repository"""
	subprocess.run(['git', '-C', GIT_PATH, 'commit', '-a', '-m', message])

def daily_tag(message=DAILY_TAG_MESSAGE, tag_name=DATE):
	"""Set tag for the commit"""
	subprocess.run(['git', '-C', GIT_PATH, 'tag', '-a', tag_name, '-m', message])