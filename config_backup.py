#!/usr/bin/env python3
from functions import *
from functions.common import *
from functions.variables import *

"""
Script to gather configuraiton from nodes and upload them to git repository.
Script is ready to use inside Kubernetes cluster with custom docker image.
"""

# Set Git global settings inside container
git_set_global_settings()

# Pull current config files stored in git repository
print('--- Pulling git repo')
git_pull()

### Backup configuration of nodes provided below
# Cisco vEPC instances
print('--- Config backup of Cisco vEPC nodes')
config_backup(vepc, vepcs, USERNAME, PASSWORD)
# Cisco switches
print('--- Config backup of Cisco switches')
config_backup(switch, switches, USERNAME, PASSWORD)
# Bind DNS nodes
print('--- Config backup of Bind DNS nodes')
dns_backup(dns, dns, USERNAME, PASSWORD)

# Add all files to current commit
print('--- Adding files to current commit')
git_add()

# Commit changes to repository
print('--- Commiting changes')
git_commit()

# Set tag for the commit
print('--- Setting daily tag')
daily_tag()

# Push changes to git repository
print('--- Pushing changes to git repo')
git_push('--follow-tags')