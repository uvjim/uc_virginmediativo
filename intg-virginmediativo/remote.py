"""Remote entity."""

# region #-- imports --#
import asyncio
import logging
import math
from enum import StrEnum
from sre_parse import State
from typing import Any

from config import VmTivoDevice
from const import AVAILABLE_COMMANDS, CodeDefinition, CodeTypes
from logger import log, log_formatter
from pyee import AsyncIOEventEmitter
from pyvmtivo.client import Client, Device
from pyvmtivo.exceptions import VirginMediaCommandTimeout, VirginMediaConnectionReset
from ucapi import EntityTypes, Remote
from ucapi.api_definitions import StatusCodes
from ucapi.media_player import Commands as MediaPlayerCommands
from ucapi.remote import Attributes, Commands, Features, States
from ucapi.ui import (
    Buttons,
    DeviceButtonMapping,
    EntityCommand,
    Location,
    Size,
    UiItem,
    UiPage,
)

# endregion

_LOG: logging.Logger = logging.getLogger(__name__)
_LOG_INC_DATETIME: bool = True


class Events(StrEnum):
    """Available events."""

    STATE_CHANGED = "uvjim_state_changed"


class RemoteState(StrEnum):
    """What is the remote doing?"""

    DVR = "dvr"
    LIVE = "live"
    PAUSED = "paused"
    SPEEDING = "speeding"


class TivoRemote(Remote):
    """TiVo remote representation."""

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def __init__(self, device_config: VmTivoDevice) -> None:
        """Initialise."""

        self._remote_state: RemoteState = RemoteState.LIVE
        self._tivo_config: VmTivoDevice = device_config
        self._client: Client = Client(self._tivo_config.address, self._tivo_config.port)
        self._client.add_data_callback(self._data_callback)

        self.events: AsyncIOEventEmitter = AsyncIOEventEmitter(
            asyncio.get_running_loop()
        )

        attributes: dict[str, Any] = {
            Attributes.STATE: (
                States.ON if self._client.device.channel_number else States.UNKNOWN
            )
        }
        button_mapping: list[DeviceButtonMapping] = [
            DeviceButtonMapping(
                button=Buttons.BACK,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.PREVIOUS),
                long_press=EntityCommand(
                    cmd_id="remote.send_cmd", params={"command": "CLEAR"}
                ),
            ),
            DeviceButtonMapping(
                button=Buttons.BLUE,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.FUNCTION_BLUE),
            ),
            DeviceButtonMapping(
                button=Buttons.CHANNEL_DOWN,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CHANNEL_DOWN),
            ),
            DeviceButtonMapping(
                button=Buttons.CHANNEL_UP,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CHANNEL_UP),
            ),
            DeviceButtonMapping(
                button=Buttons.DPAD_DOWN,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CURSOR_DOWN),
            ),
            DeviceButtonMapping(
                button=Buttons.DPAD_LEFT,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CURSOR_LEFT),
            ),
            DeviceButtonMapping(
                button=Buttons.DPAD_MIDDLE,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CURSOR_ENTER),
            ),
            DeviceButtonMapping(
                button=Buttons.DPAD_RIGHT,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CURSOR_RIGHT),
            ),
            DeviceButtonMapping(
                button=Buttons.DPAD_UP,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.CURSOR_UP),
            ),
            DeviceButtonMapping(
                button=Buttons.GREEN,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.FUNCTION_GREEN),
            ),
            DeviceButtonMapping(
                button=Buttons.HOME,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.HOME),
            ),
            DeviceButtonMapping(
                button=Buttons.NEXT,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.FAST_FORWARD),
            ),
            DeviceButtonMapping(
                button=Buttons.PLAY,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.PLAY_PAUSE),
                long_press=EntityCommand(cmd_id=MediaPlayerCommands.STOP),
            ),
            DeviceButtonMapping(
                button=Buttons.PREV,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.REWIND),
            ),
            DeviceButtonMapping(
                button=Buttons.RED,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.FUNCTION_RED),
            ),
            DeviceButtonMapping(
                button=Buttons.YELLOW,
                short_press=EntityCommand(cmd_id=MediaPlayerCommands.FUNCTION_YELLOW),
            ),
        ]
        features: list[Features] = [Features.ON_OFF, Features.SEND_CMD]
        simple_commands: list[str] = [
            simple_command
            for simple_command in AVAILABLE_COMMANDS.keys()
            if not isinstance(simple_command, MediaPlayerCommands)
        ]

        # region #-- define UI pages --#
        pg_digits: list[UiItem] = [
            UiItem(
                command=EntityCommand(cmd_id=f"digit_{i}"),
                location=Location(x=(i - 1) % 3, y=math.floor((i - 1) / 3)),
                size=Size(width=1, height=1),
                text=str(i),
                type="text",
            )
            for i in range(1, 10)
        ]
        pg_digits.extend(
            [
                UiItem(
                    command=EntityCommand(cmd_id=MediaPlayerCommands.RECORD),
                    location=Location(x=0, y=3),
                    size=Size(width=1, height=1),
                    text="REC",
                    type="text",
                ),
                UiItem(
                    command=EntityCommand(cmd_id=MediaPlayerCommands.DIGIT_0),
                    location=Location(x=1, y=3),
                    size=Size(width=1, height=1),
                    text="0",
                    type="text",
                ),
                UiItem(
                    command=EntityCommand(cmd_id=MediaPlayerCommands.INFO),
                    location=Location(x=2, y=3),
                    size=Size(width=1, height=1),
                    text="INFO",
                    type="text",
                ),
            ]
        )

        ui_pages: list[UiPage] = [
            UiPage(
                grid=Size(width=3, height=4),
                items=pg_digits,
                name="Numbers",
                page_id="digits",
            ),
            UiPage(
                grid=Size(width=6, height=9),
                items=[
                    # region #-- first row --#
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.MY_RECORDINGS),
                        location=Location(x=0, y=0),
                        size=Size(width=1, height=1),
                        text="DVR",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.LIVE),
                        location=Location(x=1, y=0),
                        size=Size(width=2, height=1),
                        text="LIVE",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.GUIDE),
                        location=Location(x=3, y=0),
                        size=Size(width=2, height=1),
                        text="GUIDE",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.INFO),
                        location=Location(x=5, y=0),
                        size=Size(width=1, height=1),
                        text="INFO",
                        type="text",
                    ),
                    # endregion
                    # region #-- spacer --#
                    UiItem(
                        location=Location(x=0, y=1),
                        size=Size(width=6, height=1),
                        text="",
                        type="text",
                    ),
                    # endregion
                    # region # -- second row --#
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.REWIND),
                        icon="uc:bw",
                        location=Location(x=0, y=2),
                        size=Size(width=2, height=1),
                        type="icon",
                    ),
                    UiItem(
                        command=EntityCommand(
                            cmd_id="remote.send_cmd", params={"command": "PLAY"}
                        ),
                        icon="uc:play",
                        location=Location(x=2, y=2),
                        size=Size(width=2, height=1),
                        type="icon",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.FAST_FORWARD),
                        icon="uc:ff",
                        location=Location(x=4, y=2),
                        size=Size(width=2, height=1),
                        type="icon",
                    ),
                    # endregion
                    # region #-- third row --#
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.RECORD),
                        icon="uc:rec",
                        location=Location(x=0, y=3),
                        size=Size(width=2, height=1),
                        type="icon",
                    ),
                    UiItem(
                        command=EntityCommand(
                            cmd_id="remote.send_cmd", params={"command": "PAUSE"}
                        ),
                        icon="uc:pause",
                        location=Location(x=2, y=3),
                        size=Size(width=2, height=1),
                        type="icon",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.STOP),
                        icon="uc:stop",
                        location=Location(x=4, y=3),
                        size=Size(width=2, height=1),
                        type="icon",
                    ),
                    # endregion
                    # region #-- spacer --#
                    UiItem(
                        location=Location(x=0, y=4),
                        size=Size(width=6, height=1),
                        text="",
                        type="text",
                    ),
                    # endregion
                    # region  #-- fourth row --#
                    UiItem(
                        command=EntityCommand(
                            cmd_id="remote.send_cmd", params={"command": "CLEAR"}
                        ),
                        location=Location(x=0, y=5),
                        size=Size(width=1, height=1),
                        text="CLEAR",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(
                            cmd_id="remote.send_cmd", params={"command": "THUMBSDOWN"}
                        ),
                        location=Location(x=1, y=5),
                        size=Size(width=2, height=1),
                        text="ThDown",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(
                            cmd_id="remote.send_cmd", params={"command": "THUMBSUP"}
                        ),
                        location=Location(x=3, y=5),
                        size=Size(width=2, height=1),
                        text="ThUp",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.HOME),
                        location=Location(x=5, y=5),
                        size=Size(width=1, height=1),
                        text="HOME",
                        type="text",
                    ),
                    # region #-- spacer --#
                    UiItem(
                        location=Location(x=0, y=6),
                        size=Size(width=6, height=1),
                        text="",
                        type="text",
                    ),
                    # endregion
                    # region #-- fifth row --#
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.OFF),
                        location=Location(x=0, y=7),
                        size=Size(width=1, height=1),
                        text="OFF",
                        type="text",
                    ),
                    UiItem(
                        command=EntityCommand(cmd_id=MediaPlayerCommands.ON),
                        location=Location(x=5, y=7),
                        size=Size(width=1, height=1),
                        text="ON",
                        type="text",
                    ),
                    # endregion
                ],
                name="Misc.",
                page_id="misc",
            ),
        ]
        # endregion

        super().__init__(
            f"{EntityTypes.REMOTE.value}.{self._tivo_config.id}",
            self._tivo_config.name,
            features,
            attributes,
            button_mapping=button_mapping,
            simple_commands=simple_commands,
            ui_pages=ui_pages,
        )

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def _data_callback(
        self,
        device: Device,
    ) -> None:
        """"""
        cur_state: States = States.UNKNOWN
        if device.channel_number is not None:
            cur_state = States.ON

        self.events.emit(
            Events.STATE_CHANGED,
            self.id,
            {Attributes.STATE: cur_state},
        )

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def command(
        self, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        """"""

        repeat: int = params.get("repeat", 1)
        ret: StatusCodes = StatusCodes.OK
        for _ in range(0, repeat):
            ret = await self.async_handle_command(cmd_id, params)

        return ret

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_handle_command(
        self, cmd_id: str, params: dict[str, Any] | None = None
    ) -> StatusCodes:
        """"""

        _LOG.debug(
            log_formatter(
                f"on entry remote is: {self._remote_state.value}",
                include_datetime=_LOG_INC_DATETIME,
            )
        )

        delay: int = int(params.get("delay", 0)) / 1000
        command: str | None
        if cmd_id == Commands.OFF:
            command = MediaPlayerCommands.OFF
        elif cmd_id == Commands.ON:
            command = MediaPlayerCommands.ON
        elif cmd_id == Commands.SEND_CMD:
            if params is not None:
                command = params.get("command")
                if command not in AVAILABLE_COMMANDS.keys():
                    return StatusCodes.NOT_IMPLEMENTED
        elif cmd_id == Commands.SEND_CMD_SEQUENCE:
            cmd_sequence: list[MediaPlayerCommands | str] = params.get("sequence", [])
            for cmd in cmd_sequence:
                ret: StatusCodes = await self.async_handle_command(
                    Commands.SEND_CMD.value,
                    {"command": cmd, "delay": delay, "hold": params.get("hold", 0)},
                )
            return ret
        else:
            return StatusCodes.NOT_IMPLEMENTED

        code_def: CodeDefinition | None
        err: bool = False
        try:
            if (code_def := AVAILABLE_COMMANDS.get(command, None)) is None:
                return StatusCodes.NOT_IMPLEMENTED

            if command == MediaPlayerCommands.PLAY_PAUSE:
                if self._remote_state != RemoteState.LIVE:
                    _LOG.debug(
                        log_formatter(
                            "switching command to PLAY",
                            include_datetime=_LOG_INC_DATETIME,
                        )
                    )
                    command = "PLAY"
                    code_def = AVAILABLE_COMMANDS.get(command, None)

            if code_def.type == CodeTypes.IRCODE:
                args = [
                    code_def.code,
                    (
                        code_def.wait
                        if self._remote_state is RemoteState.LIVE
                        else False
                    ),
                ]
                func = self._client.send_ircode

            if code_def.type == CodeTypes.TELEPORT:
                args = [code_def.code]
                func = self._client.send_teleport

            async with self._client:
                for idx_repeat in range(1, code_def.repeat + 1):
                    await func(*args)
                    if (
                        idx_repeat != code_def.repeat
                        and code_def.wait_repeat is not None
                    ):
                        _LOG.debug(log_formatter(f"sleeping {code_def.wait_repeat}s"))
                        await asyncio.sleep(code_def.wait_repeat)

            if code_def.state:
                self.events.emit(
                    Events.STATE_CHANGED,
                    self.id,
                    {Attributes.STATE: code_def.state},
                )

        except Exception as exc:
            if code_def.wait:
                if str(command).lower().startswith("digit_") and isinstance(
                    exc, VirginMediaCommandTimeout
                ):
                    _LOG.debug(
                        log_formatter(
                            "suppressing timeout", include_datetime=_LOG_INC_DATETIME
                        )
                    )
            else:
                _LOG.error(log_formatter(exc, include_datetime=_LOG_INC_DATETIME))
                err = True

        if err:
            return StatusCodes.SERVICE_UNAVAILABLE

        if command in [MediaPlayerCommands.LIVE, "PLAY", MediaPlayerCommands.STOP]:
            self._remote_state = RemoteState.LIVE
        elif command in [MediaPlayerCommands.FAST_FORWARD, MediaPlayerCommands.REWIND]:
            self._remote_state = RemoteState.SPEEDING
        elif command == MediaPlayerCommands.PLAY_PAUSE:
            self._remote_state = RemoteState.PAUSED

        if delay > 0:
            _LOG.debug(
                log_formatter(
                    f"waiting for the specified delay time: {delay}s",
                    include_datetime=_LOG_INC_DATETIME,
                )
            )
            await asyncio.sleep(delay)

        _LOG.debug(
            log_formatter(
                f"on exit remote is: {self._remote_state.value}",
                include_datetime=_LOG_INC_DATETIME,
            )
        )

        return StatusCodes.OK

    async def get_state(self, connect: bool = True) -> States:
        """Determine the current state of the TiVo"""
        ret = States.OFF
        try:
            if connect:
                async with self._client:
                    await self._client.wait_for_data()
            # if self._client.device.channel_number is not None:
            ret = States.ON
        except VirginMediaConnectionReset as exc:
            if self.attributes.get(Attributes.STATE) != States.OFF:
                if self._remote_state != RemoteState.DVR:
                    _LOG.debug(
                        log_formatter(
                            f"assuming on: {exc} (possibly on DVR)",
                            include_datetime=_LOG_INC_DATETIME,
                        )
                    )
                    self._remote_state = RemoteState.DVR
                ret = States.ON
            else:
                ret = States.OFF
        except VirginMediaCommandTimeout as exc:
            _LOG.debug(
                log_formatter(
                    f"assuming off: {exc}", include_datetime=_LOG_INC_DATETIME
                )
            )
            ret = States.OFF
        except Exception as exc:
            _LOG.error(log_formatter(exc, include_datetime=_LOG_INC_DATETIME))
            ret = States.UNKNOWN

        return ret
