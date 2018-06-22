import os
import threading

import ruamel.yaml

from . import const, utils


class Config:
    """Class to represent dups config."""

    __instance = None
    __lock = threading.RLock()

    _data = None

    def __init__(self):
        """Create a new config instance.
           Using `Config.get`_ is the preferred way.
        """
        self.reload()

    @classmethod
    def get(cls):
        """Get a instance of `Config`_.

        Returns:
            Config: A existing (or new if it's the first call)
                instance of `Config`_
        """
        if not cls.__instance:
            cls.__instance = cls()
        return cls.__instance

    def reload(self):
        """Reload the config data from file."""
        with Config.__lock:
            config_data = dict()
            if os.path.isfile(const.CONFIG_PATH):
                with open(const.CONFIG_PATH, 'r') as f:
                    config_data = ruamel.yaml.YAML(typ='safe').load(f.read())
            else:
                dir_ = os.path.dirname(const.CONFIG_PATH)
                if not os.path.exists(dir_):
                    os.makedirs(dir_)

                return

            template_data = dict()
            with open(const.CONFIG_TEMPLATE_PATH, 'r') as f:
                template_data = ruamel.yaml.YAML(typ='safe').load(f.read())

            self._data = utils.dict_merge(template_data, config_data)

    def save(self):
        """Save the current configuration to file."""
        with Config.__lock:
            yaml = ruamel.yaml.YAML()
            yaml.indent(mapping=2, sequence=4, offset=2)

            with open(const.CONFIG_PATH, 'w+') as f:
                yaml.dump(self._data, f)

    def _add_list_data(self, key, values):
        """Add the given values to the list identified by the given key.

        Args:
            key (str): Name of the list to add all values to.
            values (list): Items to add to the given list.
        """
        if not isinstance(self._data[key], dict):
            self._data[key] = dict()

        for val in values:
            if os.path.isfile(val):
                val = os.path.abspath(val)
                type_ = 'file'
            elif os.path.isdir(val):
                val = os.path.abspath(val)
                type_ = 'folder'
            else:
                type_ = 'pattern'

            self._data[key][val] = type_

    def _remove_list_data(self, key, values):
        """Remove the given values from the list identified by the given key.

        Args:
            key (str): Name of the list to remove all values from.
            values (list): Items to remove from the given list.
        """
        if not isinstance(self._data[key], dict):
            return None

        for val in values:
            if os.path.isfile(val) or os.path.isdir(val):
                val = os.path.abspath(val)

            if val in self._data[key]:
                del self._data[key][val]

    @property
    def target(self):
        """dict: The configured target with expanded paths."""
        t = self._data['target']

        if t['path']:
            t['path'] = os.path.expanduser(t['path'])

        if t['ssh_key_file']:
            t['ssh_key_file'] = os.path.expanduser(t['ssh_key_file'])

        return t

    @property
    def includes(self):
        """dict: The configured includes."""
        if not self._data['includes']:
            return dict()
        return self._data['includes']

    def add_includes(self, values):
        """Add new items to the list of includes.

        Args:
            values (list): Files, folders and/or patterns to add to the list
                of includes.
        """
        self._add_list_data('includes', values)
        self.save()

    def remove_includes(self, values):
        """Remove the given items from the list of includes.

        Args:
            values (list): Files, folders and/or patterns to remove from the
                list of includes.
        """
        self._remove_list_data('includes', values)
        self.save()

    @property
    def excludes(self):
        """dict: The configured excludes."""
        if not self._data['excludes']:
            return dict()
        return self._data['excludes']

    def add_excludes(self, values):
        """Add new items to the list of excludes.

        Args:
            values (list): Files, folders and/or patterns to add to the list
                of excludes.
        """
        self._add_list_data('excludes', values)
        self.save()

    def remove_excludes(self, values):
        """Remove the given items from the list of excludes.

        Args:
            values (list): Files, folders and/or patterns to remove from the
                list of excludes.
        """
        self._remove_list_data('excludes', values)
        self.save()

    @property
    def notify(self):
        """bool: The configured notify state."""
        return self._data['notify']

    @property
    def rsync(self):
        """dict: The configured rsync options."""
        return self._data['rsync']

    @property
    def logging(self):
        """dict: The configured logging options."""
        return self._data['logging']
