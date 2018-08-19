"""
Constant variables used throught the application.

Attributes:
    HERE (str): Absolute path to the source directory of dups.

    APP_NAME (str): Name of the application.
    APP_ICON (str): Name of the applications icon.

    DBUS_NAME (str): Name used to register with dbus.
    DBUS_PATH (str): Path used to register with dbus.

    CONFIG_TEMPLATE_PATH (str): Absolute path to the template config file.
    DEFAULT_RESTORE_PATH (str): Path to the default restore directory.
"""
import os

HERE = os.path.dirname(os.path.realpath(__file__))

APP_NAME = 'dups'
APP_ID = 'de.linuxwhatelse.dups'
APP_ICON = 'security-high'  # Until we have our own icon

DBUS_NAME = 'de.linuxwhatelse.dups.daemon'
DBUS_PATH = '/de/linuxwhatelse/dups'

CONFIG_TEMPLATE_FILE = os.path.join(HERE, 'data', 'config.yaml')
DEFAULT_RESTORE_PATH = '/'

SSH_WRAPPER_SCRIPT = os.path.join(HERE, 'data', 'ssh')
