import logging
import sys
import threading
import traceback

import dbus
import dbus.mainloop.glib
import dbus.service
import gi.repository.GLib

from . import config, const, helper, utils

LOGGER = logging.getLogger(__name__)


class Daemon(dbus.service.Object):
    """Class to register a service with dbus."""

    def __init__(self, bus, path):
        """Create a new instance of `Daemon`_.
           Use `Daemon.run`_ to start a automatically created instance.

        Args:
            bus (dbus.SessionBus): Instance of a `dbus.SessionBus`_.
            path (str): The path to register on dbus with.
        """
        dbus.service.Object.__init__(self, bus, path)

    @classmethod
    def run(cls):
        """Register with dbus and start the daemon."""
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        bus = dbus.SessionBus()
        try:
            # Needs to be assigned
            name = dbus.service.BusName(  # noqa: F841
                const.DBUS_NAME, bus, do_not_queue=True)

        except dbus.NameExistsException:
            print('A instance is already running.')
            sys.exit(1)

        mainloop = gi.repository.GLib.MainLoop()

        daemon = cls(bus, const.DBUS_PATH)
        daemon.mainloop = mainloop

        try:
            print('Daemon started. Awaiting requests...')
            mainloop.run()

        except KeyboardInterrupt:
            print('Shuttind down...')
            sys.exit(0)

    @dbus.service.method(const.DBUS_NAME, in_signature='b')
    def backup(self, dry_run):
        """Start a new backup task in a separate thread.

        Args:
            dry_run (bool): Whether or not to perform a trial run with no
                changes made.
        """
        dry_run = bool(dry_run)

        def _backup():
            try:
                config.Config.get().reload()

                helper.notify('Starting new backup')
                bak, status = helper.create_backup(dry_run)
                helper.notify('Finished backup', status.message)

            except Exception as e:
                helper.notify('Coulnd\'t start backup', str(e),
                              utils.NUrgency.CRITICAL)
                LOGGER.info(e)
                LOGGER.debug(traceback.format_exc())

        threading.Thread(target=_backup).start()

    @dbus.service.method(const.DBUS_NAME, in_signature='asssb')
    def restore(self, items, name, target, dry_run):
        """Start a new restore task in a separate thread.

        Args:
            items (list): List of files and folders to be restored.
                If `None` or empty, the entire backup will be restored.
            name (str): Name of the backup to use for the restore.
            target (str): Where to restore the data to.
            dry_run (bool): Whether or not to perform a trial run with no
                changes made.
        """
        items = list(str(i) for i in items)
        dry_run = bool(dry_run)

        def _restore():
            try:
                config.Config.get().reload()

                helper.notify('Starting restore')
                bak, status = helper.restore_backup(items, name, target,
                                                    dry_run)
                helper.notify('Finished restore', status.message)

            except Exception as e:
                helper.notify('Coulnd\'t start restore', str(e),
                              utils.NUrgency.CRITICAL)
                LOGGER.info(e)
                LOGGER.debug(traceback.format_exc())

        threading.Thread(target=_restore).start()


class Client(object):
    """Class to interact with a running daemon instance.

    Note:
        Methods will automatically be resolved with the running daemon.
        Therefore you can just call a method on this `Client`_ instance and
        it will be propergated to the daemon.
    """
    __instance = None

    def __init__(self):
        """Create a new client instance.
           Using `Client.get`_ is the preferred way.
        """
        self._bus = dbus.SessionBus()
        self._proxy = self._bus.get_object(const.DBUS_NAME, const.DBUS_PATH)
        self._iface = dbus.Interface(self._proxy, const.DBUS_NAME)

    @classmethod
    def get(cls):
        """Get a instance of `Client`_.

        Returns:
            Client: A existing (or new if it's the first call)
                instance of `Client`_.
        """
        if not cls.__instance:
            cls.__instance = cls()
        return cls.__instance

    def __getattribute__(self, name):
        if name in ('_bus', '_proxy', '_iface'):
            return object.__getattribute__(self, name)

        return getattr(self._iface, name)
