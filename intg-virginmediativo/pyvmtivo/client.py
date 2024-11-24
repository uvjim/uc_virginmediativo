"""Communication with the TiVo device."""

# region #-- imports --#
import asyncio
import contextlib
import logging
import re
from typing import Callable

from .const import (
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_CONNECT_PORT,
    DEFAULT_CONNECT_TIMEOUT,
)
from .exceptions import (
    VirginMediaCommandTimeout,
    VirginMediaConnectionReset,
    VirginMediaError,
    VirginMediaInvalidChannel,
    VirginMediaInvalidCommand,
    VirginMediaInvalidKey,
    VirginMediaNotLive,
    format_error_message,
)
from .logger import Logger

# endregion

_LOGGER = logging.getLogger(__name__)


class Device:
    """Represents the attributes of the device."""

    def __init__(self, host: str, port: int):
        """Initialise."""
        self._host: str = host
        self._port: int = port

        self._channel_number: int | None = None
        self._prev_channel_number: int | None = None

    @property
    def host(self) -> str:
        """Return the device hostname."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port number used for connecting to the device."""
        return self._port

    @property
    def channel_number(self) -> int | None:
        """Return the current channel number."""
        return self._channel_number

    @channel_number.setter
    def channel_number(self, value: int | None) -> None:
        """Set the channel number."""
        if value != self._channel_number:
            self._prev_channel_number = self._channel_number
            self._channel_number = value

    @property
    def previous_channel_number(self) -> int | None:
        """Return the previous channel number."""
        return self._prev_channel_number


class Client:
    """Represent a connection to the TiVo device."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_CONNECT_PORT,
        timeout: float = DEFAULT_CONNECT_TIMEOUT,
        command_timeout: float = DEFAULT_COMMAND_TIMEOUT,
    ) -> None:
        """Initialise."""
        self._command_timeout: float | None = command_timeout or DEFAULT_COMMAND_TIMEOUT
        self._data_callback: list = []
        self._host: str = host
        self._lock_read: asyncio.Lock = asyncio.Lock()
        self._log_formatter: Logger = Logger()
        self._port: int = port
        self._timeout: float = timeout
        self._reader: asyncio.StreamReader | None = None
        self._tivo: Device = Device(host=self._host, port=self._port)
        self._writer: asyncio.StreamWriter | None = None

    async def __aenter__(self) -> "Client":
        """Entry point for the Context Manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit point for the Context Manager."""
        await self.disconnect()

    # region #-- private methods --#
    async def _send(self, data: str, wait_for_reply: bool = True) -> None:
        """Send request to the device.

        :param data: data to send
        :param wait_for_reply: True to wait for the reply
        :return: None
        """
        data = f"{data}\r".upper()
        try:
            if self._writer:
                self._writer.write(data.encode())
                await self._writer.drain()
                if wait_for_reply:
                    await self.wait_for_data()
        except Exception as err:
            _LOGGER.debug(
                self._log_formatter.format("type: %s, message: %s"), type(err), err
            )
            if isinstance(err, asyncio.TimeoutError):
                raise VirginMediaCommandTimeout from err

            if isinstance(err, VirginMediaError):
                raise err from None

            raise VirginMediaError(format_error_message(err)) from err

    # endregion

    # region #-- public methods --#
    async def connect(self) -> None:
        """Create a connection to the device."""
        _LOGGER.debug(self._log_formatter.format("entered"))
        try:
            _LOGGER.debug(
                self._log_formatter.format(
                    "connecting to %s on port %d with timeout %0.1fs"
                ),
                self._host,
                self._port,
                self._timeout,
            )
            open_future = asyncio.open_connection(self._host, self._port)
            self._reader, self._writer = await asyncio.wait_for(
                open_future, self._timeout
            )
            _LOGGER.debug(
                self._log_formatter.format("connected to %s on port %d"),
                self._host,
                self._port,
            )
        except (
            OSError,
            ConnectionError,
            ConnectionResetError,
            asyncio.TimeoutError,
        ) as err:
            _LOGGER.debug(
                self._log_formatter.format("type: %s, message: %s"), type(err), err
            )
            if isinstance(err, asyncio.TimeoutError):
                raise VirginMediaCommandTimeout from err
            raise VirginMediaError(format_error_message(err)) from err

        _LOGGER.debug(self._log_formatter.format("exited"))

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        _LOGGER.debug(self._log_formatter.format("entered"))
        if self._writer:
            _LOGGER.debug(
                self._log_formatter.format("disconnecting from %s on port %d"),
                self._host,
                self._port,
            )
            self._writer.close()
            await self._writer.wait_closed()
            _LOGGER.debug(
                self._log_formatter.format("disconnected from %s on port %d"),
                self._host,
                self._port,
            )
            self._writer = None
            self._reader = None
        else:
            _LOGGER.debug(
                self._log_formatter.format("not currently connected to %s on port %d"),
                self._host,
                self._port,
            )

        _LOGGER.debug(self._log_formatter.format("exited"))

    async def send_ircode(self, code: str, wait_for_reply: bool = True) -> None:
        """Send an infrared code to the device.

        :param code: the IR code to send
        :param wait_for_reply: True if intending to wait for a response
        :return: None
        """
        _LOGGER.debug(self._log_formatter.format("entered"))
        try:
            _LOGGER.debug(self._log_formatter.format("sending ircode: %s"), code)
            await self._send(f"ircode {code}", wait_for_reply=wait_for_reply)
        except VirginMediaError as err:
            if str(err).lower() == "invalid_key":
                raise VirginMediaInvalidKey(key_code=code) from err

            raise err from None
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(self._log_formatter.format("%s"), err)
        else:
            _LOGGER.debug(self._log_formatter.format("ircode sent: %s"), code)

        _LOGGER.debug(self._log_formatter.format("exited"))

    async def send_keyboard(self, code: str, wait_for_reply: bool = True) -> None:
        """Send a keyboard code to the device.

        :param code: the keyboard code to send
        :param wait_for_reply: True to wait for a response after sending
        :return: None
        """
        _LOGGER.debug(self._log_formatter.format("entered"))
        try:
            _LOGGER.debug(self._log_formatter.format("sending keyboard: %s"), code)
            await self._send(f"keyboard {code}", wait_for_reply=wait_for_reply)
        except VirginMediaError as err:
            _LOGGER.warning(
                self._log_formatter.format("type: %s, message: %s"), type(err), err
            )
            if str(err).lower() == "invalid_key":
                raise VirginMediaInvalidKey(key_code=code) from err
        else:
            _LOGGER.debug(self._log_formatter.format("keyboard sent: %s"), code)

        _LOGGER.debug(self._log_formatter.format("exited"))

    async def send_teleport(self, code: str) -> None:
        """Send a teleport code to the device.

        :param code: the teleport code to send
        :return: None
        """
        _LOGGER.debug(self._log_formatter.format("entered"))
        try:
            _LOGGER.debug(self._log_formatter.format("sending teleport: %s"), code)
            await self._send(f"teleport {code}")
        except VirginMediaError as err:
            if str(err).lower() == "invalid_command":
                raise VirginMediaInvalidCommand(command=code) from err
        else:
            _LOGGER.debug(self._log_formatter.format("teleport sent: %s"), code)

        _LOGGER.debug(self._log_formatter.format("exited"))

    async def set_channel(self, channel_number: int) -> None:
        """Change the channel on the device.

        :param channel_number: the channel number to change to
        :return: None
        """
        _LOGGER.debug(self._log_formatter.format("entered"))
        try:
            _LOGGER.debug(
                self._log_formatter.format("setting channel number to: %d"),
                channel_number,
            )
            await self._send(f"setch {channel_number}")
        except VirginMediaError as err:
            if str(err).lower() == "no_live":
                raise VirginMediaNotLive from err
            if str(err).lower() == "invalid_channel":
                raise VirginMediaInvalidChannel(channel_number=channel_number) from err
            raise
        else:
            _LOGGER.debug(
                self._log_formatter.format("channel number set to: %d"), channel_number
            )

        _LOGGER.debug(self._log_formatter.format("exited"))

    async def wait_for_data(self) -> None:
        """Process the data from the device.

        The device only returns an error or the current channel number
        """
        _LOGGER.debug(self._log_formatter.format("entered"))
        async with self._lock_read:
            buffer_size = 1024
            try:
                data_future = self._reader.read(buffer_size)
                data = await asyncio.wait_for(
                    data_future, timeout=self._command_timeout
                )
            except Exception as err:
                if isinstance(err, asyncio.TimeoutError):
                    # self._tivo.channel_number = None
                    raise VirginMediaCommandTimeout from err

                _LOGGER.warning(
                    self._log_formatter.format("type: %s, message: %s"),
                    type(err),
                    err,
                )
                raise VirginMediaError(format_error_message(err)) from None

            _LOGGER.debug(self._log_formatter.format("raw data: %s"), data)

            if not data:
                # self._tivo.channel_number = None
                raise VirginMediaConnectionReset from None

            data = data.decode().strip()
            if data.startswith("CH_STATUS"):
                regex = r"\d{4}"
                regex_match: re.Match = re.search(regex, data)
                if regex_match:
                    self._tivo.channel_number = int(regex_match.group(0))
            elif data.startswith("CH_FAILED"):
                raise VirginMediaError(data.split(" ")[-1])
            elif data == "INVALID_KEY":
                raise VirginMediaError(data)
            elif data == "INVALID_COMMAND":
                raise VirginMediaError(data)

            if self._data_callback:
                _LOGGER.debug(self._log_formatter.format("executing callbacks"))
                for func in self._data_callback:
                    if isinstance(func, Callable):
                        func(self._tivo)

        _LOGGER.debug(self._log_formatter.format("exited"))

    def add_data_callback(self, callback: Callable) -> None:
        """Add a callback for execution after data has been retrieved."""
        _LOGGER.debug(self._log_formatter.format("entered"))
        self._data_callback.append(callback)
        _LOGGER.debug(self._log_formatter.format("exited"))

    def remove_data_callback(self, callback: Callable) -> None:
        """Remove the given callback from being processed."""
        _LOGGER.debug(self._log_formatter.format("entered"))
        with contextlib.suppress(ValueError):
            self._data_callback.remove(callback)
        _LOGGER.debug(self._log_formatter.format("exited"))

    # endregion

    # region #-- properties --#
    @property
    def device(self) -> Device:
        """Device class."""
        return self._tivo

    @property
    def is_connected(self) -> bool:
        """Check if the device is connected.

        :return: True if connected, False otherwise
        """
        ret: bool = False
        if self._writer:
            ret = not self._writer.is_closing()

        return ret

    # endregion
