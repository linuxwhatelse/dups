"""
Constant variables used throught the application.

Attributes:
    HERE (str): Absolute path to the source directory of dups.

    APP_NAME (str): Name of the application.
    APP_ICON (str): Name of the applications icon.

    CONFIG_PATH (str): Absolute path to the users config file.
    CONFIG_TEMPLATE_PATH (str): Absolute path to the template config file.

    CACHE_DIR (str): Absolute path to the cache directory.
    ENV_PATH (str): Absolute path to the environment file within CACHE_DIR.

    DEFAULT_RESTORE_PATH (str): Path to the default restore directory.

    DBUS_NAME (str): Name used to register with dbus.
    DBUS_PATH (str): Path used to register with dbus.
"""
import os


def _get_config_path():
    """Get a path to a config file.

    Returns: A config file path pointing to either 
        `~/.config/dups/config.yaml` or `~/.config/dups.yaml` depending on
        which one exists.
        The first option is favored.
       """
    base = os.path.expanduser('~/.config/')

    config1 = os.path.join(base, 'dups', 'config.yaml')
    config2 = os.path.join(base, 'dups.yaml')

    if os.path.exists(config1):
        return config1
    elif os.path.exists(config2):
        return config2
    else:
        os.makedirs(os.path.dirname(config1), exist_ok=True)
        return config1


HERE = os.path.dirname(os.path.realpath(__file__))

APP_NAME = 'dups'
APP_ICON = 'security-high'  # Until we have our own icon

CONFIG_TEMPLATE_PATH = os.path.join(HERE, 'data', 'config.yaml')
CONFIG_PATH = _get_config_path()

CACHE_DIR = os.path.expanduser('~/.cache/dups')
ENV_PATH = os.path.join(CACHE_DIR, 'env.json')
os.makedirs(CACHE_DIR, exist_ok=True)

DEFAULT_RESTORE_PATH = '/'

DBUS_NAME = 'de.linuxwhatelse.dups'
DBUS_PATH = '/de/linuxwhatelse/dups'
