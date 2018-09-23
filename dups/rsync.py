import logging
import os
import re
import shlex
import subprocess
from typing import List, TypeVar

LOGGER = logging.getLogger(__name__)
_RSYNC = TypeVar('_RSYNC', bound='rsync')


class Path(object):
    """Represents a local or remote path to be used by `Rsync`_."""

    def __init__(self, path, host=None):
        """Create a new instance of `Path`_.

        Args:>
            path (str): Path to the local/remote file/folder.
            host (str): The hostname if it's a remote item.
        """
        self.path = path
        self.host = host

    @property
    def is_local(self):
        """bool: Whether or not this `Path`_ refers to a local file."""
        return self.host in ('', None)

    @property
    def resolved(self):
        """str: If local, the path origianlly provided.
           If remote, <host>:<path>
        """
        if self.is_local:
            return self.path

        return '{host}:{dest}'.format(host=self.host, dest=self.path)


class Status(object):
    """Represents the status of a concluded rsync process.

    Attributes:
        EXIT_CODES (dict): All currently known rsync exist codes mapped to
        their appropriate message.
    """
    EXIT_CODES = {
        # rsync
        0: 'Success',
        1: 'Syntax or usage error',
        2: 'Protocol incompatibility',
        3: 'Errors selecting input/output files, dirs',
        4: 'Requested action not supported: an attempt was made to \
            manipulate 64-bit files on a platform that cannot support them; \
            or an option was specified that is supported by the client \
            and not by the server.',
        5: 'Error starting client-server protocol',
        6: 'Daemon unable to append to log-file',
        10: 'Error in socket I/O',
        11: 'Error in file I/O',
        12: 'Error in rsync protocol data stream',
        13: 'Errors with program diagnostics',
        14: 'Error in IPC code',
        20: 'Received SIGUSR1 or SIGINT',
        21: 'Some error returned by waitpid()',
        22: 'Error allocating core memory buffers',
        23: 'Partial transfer due to error',
        24: 'Partial transfer due to vanished source files',
        25: 'The --max-delete limit stopped deletions',
        30: 'Timeout in data send/receive',
        35: 'Timeout waiting for daemon connection',

        # ssh
        255: 'The underlying connection failed'
    }

    _exit_code = 0

    def __init__(self, exit_code):
        """Create a new instance of `Status`_.

        Args:
            exit_code (int): The exit code for this `Status`_.

        Raises:
            ValueError: If a invalid exit code was supplied.
        """
        if exit_code not in self.EXIT_CODES:
            raise ValueError('Invalid exit code "{}"!'.format(exit_code))
        self._exit_code = exit_code

    def __str__(self):
        return self.message

    @property
    def exit_code(self):
        """int: The exit code of this `Status`_."""
        return self._exit_code

    @property
    def message(self):
        """str: The message of this `Status`_."""
        return self.EXIT_CODES[self._exit_code]

    @property
    def is_complete(self):
        """bool: If this `Status`_ can be considered as completed sync."""
        return self._exit_code in (0, 23, 24)


class rsync(object):
    """Class to send/receive data using rsync."""

    __instances = dict()

    _proc = None
    _exit_code = None

    rsync_bin = '/usr/bin/rsync'
    ssh_bin = '/usr/bin/ssh'

    ssh_config_file = '~/.ssh/config'

    acls = True
    xattrs = True
    prune_empty_dirs = True
    out_format = '%t %i %n'

    dry_run = True

    @classmethod
    def get(cls, name=__name__) -> _RSYNC:
        """Get a instance of `rsync`_.

        Args:
            name (str): A name for this instance.

        Returns:
            rsync: A existing (or new if it's the first call)
                instance of `rsync`_.
        """
        if name not in cls.__instances:
            cls.__instances[name] = cls()
        return cls.__instances[name]

    @property
    def cmd(self) -> list:
        """str: The base rsync command used for synchronisation."""
        cmd = [
            self.rsync_bin, '--archive', '--relative', '--human-readable',
            '--stats', '--verbose'
        ]

        if self.dry_run:
            # I want "--dry-run" to be the first argument.
            cmd.insert(1, '--dry-run')

        if self.out_format:
            cmd.extend(('--out-format', shlex.quote(self.out_format)))

        if self.acls:
            cmd.append('--acls')

        if self.xattrs:
            cmd.append('--xattrs')

        if self.prune_empty_dirs:
            cmd.append('--prune-empty-dirs')

        return cmd

    @property
    def ssh_cmd(self) -> list:
        cmd = [
            self.ssh_bin, '-o', 'StrictHostKeyChecking=no', '-o',
            'NumberOfPasswordPrompts=0'
        ]

        if self.ssh_config_file and os.path.exists(self.ssh_config_file):
            cmd.extend(('-F', shlex.quote(self.ssh_config_file)))

        return cmd

    def _exec(self, command):
        """Execute the given comman.

        Args:
            command (list): List of arguments forming a full command.

        Yields:
            str: Each line of the commands output.

        Raises:
            RuntimeError: If a process is already running.
        """
        if self._proc:
            raise RuntimeError('A process is already running!')

        command = ' '.join(command)

        LOGGER.info('Executing rsync:')
        LOGGER.info(command)

        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, bufsize=1,
                              universal_newlines=True) as proc:
            self._proc = proc
            self._exit_code = None

            for line in iter(proc.stdout.readline, ''):
                yield line.rstrip('\n').strip('"')

            proc.communicate()
            self._exit_code = proc.returncode

            proc.stdout.close()
            proc.wait()

        self._proc = None

    def _escape(self, path):
        """Escape all characters except for a select view.

        Args:
            path (str): Path to escape.

        Returns:
            str: Escaped version of the provided path.
        """
        return re.sub(r'([^a-zA-Z0-9,._+:@%/\-*])', r'\\\1', path)

    def sync(self, target: Path, includes: [List[str], List[Path]],
             excludes=None, link_dest=None) -> Status:
        """Send the given files to the given target.

        Args:
            target (Path): A instance of `Path`_ representing where to
                synchronize to.
            includes (list|Path): List of files, folders, and patterns to
                include.
            excludes (list): List of files, folders, and patterns to exclude.
            link_dest (str): Absolute path to a directory used for hadlinks
                in case files haven't changed.
                If `None`_, don't link with a directory.

        Returns:
            Status: A instance of `Status`_.
        """
        cmd = self.cmd
        ssh_cmd = self.ssh_cmd

        if not excludes:
            excludes = []

        cmd[1:1] = ['-e', shlex.quote(' '.join(ssh_cmd))]

        # Ensure PWD is "/" so source patterns always get expanded from the
        # same base directory.
        cmd[0:0] = ['cd', '/;']

        includes = list(
            self._escape(i.resolved) if isinstance(i, Path) else self.
            _escape(i) for i in includes)

        tmp = []
        for e in excludes:
            tmp.extend(('--exclude', shlex.quote(e)))
        excludes = tmp

        if link_dest:
            cmd.append('--delete')
            cmd.extend(('--link-dest', shlex.quote(link_dest)))

        cmd.extend(includes)
        cmd.extend(excludes)

        cmd.append(target.resolved)

        for line in self._exec(cmd):
            LOGGER.info(line)

        return Status(self._exit_code)
