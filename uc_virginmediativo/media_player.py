""""""

import ucapi
import asyncio
import logging
from typing import Any
from pyee import AsyncIOEventEmitter
from config import VmTivoDevice
from pyvmtivo.client import Client
from pyvmtivo.exceptions import VirginMediaError
import const
from enum import StrEnum

_LOG = logging.getLogger(__name__)


class Events(StrEnum):
    """Available events."""

    STATE_CHANGED = "uvjim_state_changed"


class TivoMediaPlayer:
    """"""

    def __init__(self, device: VmTivoDevice, client: Client) -> None:
        """Initialise."""

        self._client: Client = client
        self._events: AsyncIOEventEmitter = AsyncIOEventEmitter(
            asyncio.get_running_loop()
        )

        self._ucapi_entity: ucapi.MediaPlayer = ucapi.MediaPlayer(
            device.id,
            device.name,
            [
                ucapi.media_player.Features.CHANNEL_SWITCHER,
                ucapi.media_player.Features.COLOR_BUTTONS,
                ucapi.media_player.Features.DPAD,
                ucapi.media_player.Features.FAST_FORWARD,
                ucapi.media_player.Features.HOME,
                ucapi.media_player.Features.MENU,
                ucapi.media_player.Features.ON_OFF,
                ucapi.media_player.Features.PLAY_PAUSE,
                ucapi.media_player.Features.PREVIOUS,
                ucapi.media_player.Features.REWIND,
                ucapi.media_player.Features.STOP,
            ],
            {
                ucapi.media_player.Attributes.STATE: (
                    ucapi.media_player.States.ON
                    if self._client.device.channel_number
                    else ucapi.media_player.States.UNKNOWN
                ),
            },
            ucapi.media_player.DeviceClasses.SET_TOP_BOX,
            cmd_handler=self.async_cmd_handler,
        )

    async def async_cmd_handler(
        self,
        entity: ucapi.MediaPlayer,
        cmd_id: ucapi.media_player.Commands,
        params: dict[str, Any] | None,
    ) -> ucapi.StatusCodes:
        """Process commands."""
        _LOG.debug("async_cmd_handler: entered (%s)", cmd_id)

        err: bool = False

        # region #-- available command? --#
        if cmd_id not in const.AVAILABLE_COMMANDS.keys():
            return ucapi.StatusCodes.NOT_IMPLEMENTED
        # endregion

        # region #-- send the command to the device --#
        try:
            async with self._client:
                code_def: const.CodeDefinition | None
                if (code_def := const.AVAILABLE_COMMANDS.get(cmd_id, None)) is not None:
                    if code_def.type == const.CodeTypes.IRCODE:
                        for _ in range(1, code_def.repeat + 1):
                            await self._client.send_ircode(
                                code_def.code, wait_for_reply=code_def.wait
                            )
                    if code_def.type == const.CodeTypes.TELEPORT:
                        for _ in range(1, code_def.repeat + 1):
                            await self._client.send_teleport(code_def.code)

                    # region #-- update state of the media player --#
                    _state: ucapi.media_player.States | None = code_def.state
                    if cmd_id == ucapi.media_player.Commands.PLAY_PAUSE:
                        if (
                            self.ucapi_entity.attributes.get(
                                ucapi.media_player.Attributes.STATE
                            )
                            == ucapi.media_player.States.PAUSED
                        ):
                            _state = ucapi.media_player.States.PLAYING
                        else:
                            _state = ucapi.media_player.States.PAUSED
                    if _state is not None:
                        self._events.emit(
                            Events.STATE_CHANGED,
                            self.ucapi_entity.id,
                            {ucapi.media_player.Attributes.STATE: _state},
                        )
                    # endregion
                else:
                    return ucapi.StatusCodes.NOT_IMPLEMENTED
        except Exception as exc:
            _LOG.error("async_cmd_handler: %s", exc)
            err = True
        # endregion

        if err:
            return ucapi.StatusCodes.SERVER_ERROR

        _LOG.debug("async_cmd_handler: exited (%s)", cmd_id)
        return ucapi.StatusCodes.OK

    async def async_query_state(self) -> None:
        """Query for current state."""
        _LOG.debug("async_query_state: entered (%s)", self._client.device.host)
        try:
            async with self._client:
                await self._client.wait_for_data()
            if self._client.device.channel_number is not None:
                self._events.emit(
                    Events.STATE_CHANGED,
                    self.ucapi_entity.id,
                    {
                        ucapi.media_player.Attributes.STATE: ucapi.media_player.States.PLAYING
                    },
                )

        except VirginMediaError as exc:
            _LOG.error("async_query_state: %s", exc)

        _LOG.debug("async_query_state: exited (%s)", self._client.device.host)

    @property
    def events(self) -> AsyncIOEventEmitter:
        """Return the event emitter."""

        return self._events

    @property
    def ucapi_entity(self) -> ucapi.MediaPlayer:
        """Return the ucapi media player"""
        return self._ucapi_entity
