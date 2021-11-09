# Functions

This folder contains all functions used by scripts located in upper folder

## Content

- `cisco` folder with functions specific for Cisco network elements
- `ericsson` folder with functions specific for Ericsson network elements
- `common.py` common functions used by any network element
- `dns.py` functions related for BIND DNS instances
- `git.py` functions related to git management via CLI
- `logging_format.py` log formatting that should be imported in each script

Log format can be imported to each script using the following line of code
```py
from functions.logging_format import *
```