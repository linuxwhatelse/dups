import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
"""Path to the 'tests' root directory."""

sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir)))

DUPS = os.path.join(HERE, os.pardir, 'run')
"""Path to runnable dups binary"""

TMP_DIR = os.path.join(HERE, 'tmp')
"""Directory path to store temporary files for backup."""

TARGET_DIR = os.path.join('/', 'tmp', 'dups-pytest')
"""Directory path to use as backup target.
config-local.yaml and config-remote.yaml have this set as well.
"""

DATA_DIR = os.path.join(HERE, 'data')
"""Directory path holding some test data."""

SSH_HOST = 'localhost'
"""SSH Host to use for unittests."""

SSH_CONFIG = os.path.expanduser('~/.ssh/config')
"""Path to ssh config file."""

SSH_CONFIG_INVALID = os.path.expanduser('~/.ssh/config_invalid')
"""Path to invalid ssh config file."""
