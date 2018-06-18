import subprocess
import logging

from typing import List


LOGGER = logging.getLogger(__name__)


class Path:
    def __init__(self, path, host=None, port=22, username=None):
        self.path = path
        self.host = host
        self.port = port
        self.username = username

    def is_local(self):
        return None in (self.host, self.port, self.username)

    @property
    def resolved_path(self):
        dest = self.path
        if not self.is_local():
            dest = '{user}@{host}:{dest}'.format(
                user=self.username, host=self.host, dest=self.path)
        return dest


class Status:
    EXIT_CODES = {
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
    }

    _exit_code = 0

    def __init__(self, exit_code):
        if exit_code not in self.EXIT_CODES:
            raise ValueError('Invalid exit code!')
        self._exit_code = exit_code

    def __str__(self):
        return self.message

    @property
    def exit_code(self):
        return self._exit_code

    @property
    def message(self):
        return self.EXIT_CODES[self._exit_code]

    @property
    def is_complete(self):
        return self._exit_code in (0, 23, 24)


class rsync(object):
    __instance = None

    _proc = None
    _exit_code = None

    rsync_bin = '/usr/bin/rsync'
    ssh_bin = '/usr/bin/ssh'

    acls = True
    xattrs = True
    prune_empty_dirs = True
    out_format = '%t %i %n'

    dry_run = True

    def __del__(self):
        rsync.__instance = None

    @classmethod
    def get(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    @property
    def cmd(self) -> list:
        """The base rsync command used to sync"""
        cmd = [
            self.rsync_bin,
            '--archive',
            '--relative',
            '--human-readable',
            '--stats',
            '--verbose'
        ]

        if self.dry_run:
            # I want "--dry-run" to be the first argument.
            cmd.insert(1, '--dry-run')

        if self.out_format:
            cmd.append('--out-format="{}"'.format(self.out_format))

        if self.acls:
            cmd.append('--acls')

        if self.xattrs:
            cmd.append('--xattrs')

        if self.prune_empty_dirs:
            cmd.append('--prune-empty-dirs')

        return cmd

    def _exec(self, command):
        if self._proc:
            raise RuntimeError('A process is already running!')

        LOGGER.info('Executing rsync:')
        LOGGER.info(' '.join(command))
        with subprocess.Popen(command, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, bufsize=1,
                              universal_newlines=True) as proc:
            self._proc = proc
            self._exit_code = None

            for line in iter(proc.stdout.readline, ''):
                yield line.rstrip('\n')

            proc.communicate()
            self._exit_code = proc.returncode

            proc.stdout.close()
            proc.wait()

        self._proc = None

    def send(self, target: Path, includes, excludes=None,
             link_dest=None) -> Status:
        cmd = self.cmd

        if not excludes:
            excludes = list()

        if not target.is_local():
            cmd.extend(('-e', '{} -p {}'.format(self.ssh_bin, target.port)))

        includes = list('{}'.format(path) for path in includes)
        excludes = list('--exclude={}'.format(path) for path in excludes)

        if link_dest:
            cmd.append('--delete')
            cmd.append('--link-dest={}'.format(link_dest))

        cmd.extend(includes)
        cmd.extend(excludes)

        cmd.append(target.resolved_path)

        for line in self._exec(cmd):
            LOGGER.info(line)

        return Status(self._exit_code)

    def receive(self, target: Path, includes: List[Path],
                excludes=None) -> Status:
        cmd = self.cmd

        includes = list(i.resolved_path for i in includes)

        cmd.extend(includes)
        cmd.append(target.resolved_path)

        for line in self._exec(cmd):
            LOGGER.info(line)

        return Status(self._exit_code)
