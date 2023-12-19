""""""

import ucapi

import logging
from typing import Any

from config import VmTivoDevice
from pyvmtivo.client import Client
import const

_LOG = logging.getLogger(__name__)


class TivoMediaPlayer:
    """"""

    def __init__(self, device: VmTivoDevice, client: Client) -> None:
        """Initialise."""

        self._client: Client = client
        self._state: ucapi.media_player.States = ucapi.media_player.States.UNKNOWN

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
                ucapi.media_player.Attributes.STATE: self._state,
            },
            ucapi.media_player.DeviceClasses.SET_TOP_BOX,
            cmd_handler=self.async_cmd_handler,
        )

    async def async_cmd_handler(
        self, entity: ucapi.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> ucapi.StatusCodes:
        """Process commands."""
        _LOG.debug("media player cmd_handler %s", cmd_id)

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
                else:
                    return ucapi.StatusCodes.NOT_IMPLEMENTED
        except Exception as exc:
            _LOG.error("%s", exc)
            err = True
        # endregion

        if err:
            return ucapi.StatusCodes.SERVER_ERROR

        return ucapi.StatusCodes.OK

    @property
    def ucapi_entity(self) -> ucapi.MediaPlayer:
        """Return the ucapi media player"""
        return self._ucapi_entity
