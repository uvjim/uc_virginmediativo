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
        self._media_player: ucapi.MediaPlayer = ucapi.MediaPlayer(
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
                ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNKNOWN,
            },
            ucapi.media_player.DeviceClasses.SET_TOP_BOX,
            cmd_handler=self.async_cmd_handler,
        )

    async def async_cmd_handler(
        self, entity: ucapi.MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> ucapi.StatusCodes:
        """Process commands."""
        _LOG.debug("here %s", cmd_id)

        if cmd_id not in const.AVAILABLE_COMMANDS.keys():
            return ucapi.StatusCodes.NOT_IMPLEMENTED

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

        return ucapi.StatusCodes.OK

    @property
    def ucapi_mediaplayer(self) -> ucapi.MediaPlayer:
        """Return the ucapi media player"""
        return self._media_player
