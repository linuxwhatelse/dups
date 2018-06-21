class BackupNotFoundException(Exception):
    """Raised when accessing methods that require the backup to exist."""

    def __init__(self, message=None):
        if not message:
            message = 'This backup does not exist!'
        super().__init__(message)


class BackupAlreadyExistsException(Exception):
    """Raised when attempting to create a new backup with a name of an
       already existing one.
    """

    def __init__(self, message=None):
        if not message:
            message = 'This backup already exists!'
        super().__init__(message)
