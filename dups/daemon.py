import logging
import os
import sys
import threading

import dbus
import dbus.mainloop.glib
import dbus.service
import gi.repository.GLib

from . import config, const, helper, utils

LOGGER = logging.getLogger(__name__)


class Daemon(dbus.service.Object):
    """Class to register a service with dbus."""
    NOTIFY_SIGNAL = 'Notify'
    system = False

    def __init__(self, bus, path, usr):
        """Create a new instance of `Daemon`_.
           Use `Daemon.run`_ to start a automatically created instance.

        Args:
            bus (dbus.SessionBus|dbus.SystemBus): Instance of a
                `dbus.SessionBus`_ or `dbus.SessionBus`_.
            path (str): The path to register on dbus with.
        """
        dbus.service.Object.__init__(self, bus, path)

        self.system = isinstance(bus, dbus.SystemBus)

        self.path = path
        self.bus = bus
        self.usr = usr

        if not self.system:
            sbus = dbus.SystemBus()
            sbus.add_signal_receiver(self.__notification_listener,
                                     Daemon.NOTIFY_SIGNAL, const.DBUS_NAME,
                                     path=self.path)

    @classmethod
    def run(cls, usr, system=False):
        """Register with dbus and start the daemon."""
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        bus = dbus.SystemBus() if system else dbus.SessionBus()

        try:
            # Needs to be assigned
            name = dbus.service.BusName(  # noqa: F841
                const.DBUS_NAME, bus, do_not_queue=True)

        except dbus.NameExistsException:
            print('A instance is already running.')
            sys.exit(1)

        mainloop = gi.repository.GLib.MainLoop()

        path = os.path.join(const.DBUS_PATH, usr.user)

        daemon = cls(bus, path, usr)
        daemon.mainloop = mainloop

        try:
            print('Daemon started. Awaiting requests...')
            mainloop.run()

        except KeyboardInterrupt:
            print('Shutting down...')
            sys.exit(0)

    def __notification_listener(self, title, body, priority, icon):
        title = str(title)
        body = str(body)
        priority = int(priority)
        icon = str(icon)
        LOGGER.debug('Received notification from backend: %s',
                     (title, body, priority, icon))
        self._notify(title, body, priority, icon)

    @dbus.service.method(const.DBUS_NAME, in_signature='ssiss')
    def _notify(self, title, body='', priority=utils.NPriority.NORMAL,
                icon=const.APP_ICON, reason='other'):
        if not self.system:
            helper.notify(title, body, priority, icon, True, reason)
            return

        LOGGER.debug('Forwarding notification to user-session: %s', self.path)
        message = dbus.lowlevel.SignalMessage(self.path, const.DBUS_NAME,
                                              Daemon.NOTIFY_SIGNAL)
        message.append(title, body, priority, icon, reason)
        self.bus.send_message(message)

    @dbus.service.method(const.DBUS_NAME, in_signature='b')
    def backup(self, dry_run):
        """Start a new backup task in a separate thread.

        Args:
            dry_run (bool): Whether or not to perform a trial run with no
                changes made.
        """
        dry_run = bool(dry_run)

        def __backup():
            config.Config.get().reload()

            self._notify('Starting backup', reason='backup')
            status, err_msg, ex, tb = helper.error_handler(
                helper.create_backup, self.usr, dry_run)

            if status:
                priority = helper.get_rsync_notification_priority(status)
                self._notify('Finished backup', status.message, priority,
                             reason='backup')
                LOGGER.info(status.message)
            else:
                self._notify('Could not start backup', err_msg,
                             utils.NPriority.HIGH, reason='backup')
                LOGGER.debug(tb)
                LOGGER.error(err_msg)

        threading.Thread(target=__backup).start()

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

        def __restore():
            config.Config.get().reload()

            self._notify('Starting restore', reason='restore')

            status, err_msg, ex, tb = helper.error_handler(
                helper.restore_backup, self.usr, items, name, target, dry_run)

            if status:
                priority = helper.get_rsync_notification_priority(status)
                LOGGER.info(status.message)
                self._notify('Finished restore', status.message, priority,
                             reason='restore')
            else:
                LOGGER.debug(tb)
                LOGGER.error(err_msg)
                self._notify('Could not start restore', err_msg,
                             utils.NPriority.HIGH, reason='restore')

        threading.Thread(target=__restore).start()


class Client(object):
    """Class to interact with a running daemon instance.

    Note:
        Methods will automatically be resolved with the running daemon.
        Therefore you can just call a method on this `Client`_ instance and
        it will be propergated to the daemon.
    """
    __instances = {}

    def __init__(self, user, system):
        """Create a new client instance.
           Using `Client.get`_ is the preferred way.
        """
        self._bus = dbus.SystemBus() if system else dbus.SessionBus()

        path = os.path.join(const.DBUS_PATH, user)

        self._proxy = self._bus.get_object(const.DBUS_NAME, path)
        self._iface = dbus.Interface(self._proxy, const.DBUS_NAME)

    @classmethod
    def get(cls, user, system=False):
        """Get a instance of `Client`_.

        Returns:
            Client: A existing (or new if it's the first call)
                instance of `Client`_.
        """
        key = '{}.{}'.format(user, system)
        if key not in cls.__instances:
            cls.__instances[key] = cls(user, system)
        return cls.__instances[key]

    def __getattribute__(self, name):
        if name in ('_bus', '_proxy', '_iface'):
            return object.__getattribute__(self, name)

        return getattr(self._iface, name)
