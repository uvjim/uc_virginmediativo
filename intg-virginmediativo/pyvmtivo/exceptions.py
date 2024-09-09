"""Custom Exceptions."""

DEFAULT_ERROR_MESSAGES = {
    ConnectionError: "Connection error",
    BrokenPipeError: "Broken pipe",
    ConnectionAbortedError: "Connection aborted",
    ConnectionRefusedError: "Connection refused",
    ConnectionResetError: "Connection reset",
    OSError: "OS I/O error",
}


def format_error_message(error: Exception) -> str:
    """Format the error message appropriately."""
    error_message = str(error)
    if not error_message:
        error_message = DEFAULT_ERROR_MESSAGES.get(type(error))
    return error_message


class VirginMediaError(Exception):
    """General error."""


class VirginMediaCommandTimeout(VirginMediaError):
    """Command timed out."""

    def __init__(self):
        """Initialise."""
        super().__init__("Command timeout")


class VirginMediaConnectionReset(VirginMediaError):
    """Device reset the connection."""

    def __init__(self):
        """Initialise."""
        super().__init__("Connection reset")


class VirginMediaInvalidChannel(VirginMediaError):
    """Invalid channel number."""

    def __init__(self, channel_number):
        """Initialise."""
        self._channel_number = channel_number
        super().__init__(f"Invalid channel ({self.channel_number})")

    @property
    def channel_number(self) -> int:
        """Return the channel_number."""
        return self._channel_number


class VirginMediaInvalidCommand(VirginMediaError):
    """Invalid command was specified."""

    def __init__(self, command: str) -> None:
        """Initialise."""
        self._command = command
        super().__init__(f"Invalid command ({self.command})")

    @property
    def command(self) -> str:
        """Return the command."""
        return self._command


class VirginMediaInvalidKey(VirginMediaError):
    """Invalid key code."""

    def __init__(self, key_code: str):
        """Initialise."""
        self._keycode = key_code
        super().__init__(f"Invalid key ({self._keycode})")

    @property
    def key_code(self) -> str:
        """Return the key code."""
        return self._keycode


class VirginMediaNotLive(VirginMediaError):
    """Device not in LiveTV mode."""

    def __init__(self):
        """Initialise."""
        super().__init__("Not in LiveTV mode")
