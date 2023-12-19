""""""

import ucapi

import logging
from typing import Any

from config import VmTivoDevice
from pyvmtivo.client import Client
import const

_LOG = logging.getLogger(__name__)


class TivoButton:
    """"""

    def __init__(
        self, button_def: const.CodeDefinition, device: VmTivoDevice, client: Client
    ) -> None:
        """Initialise."""

        self._button_def: const.CodeDefinition = button_def
        self._client: Client = client
        self._state: ucapi.button.States = ucapi.button.States.AVAILABLE

        self._ucapi_entity: ucapi.Button = ucapi.Button(
            f"{device.id}_{button_def.code}".lower(),
            f"{device.name}: {button_def.display_name}",
            cmd_handler=self.async_cmd_handler,
        )

    async def async_cmd_handler(
        self, entity: ucapi.Button, cmd_id: str, params: dict[str, Any] | None
    ) -> ucapi.StatusCodes:
        """Process commands."""
        _LOG.debug("button cmd_handler %s", cmd_id)

        err: bool = False

        # region #-- send the command to the device --#
        try:
            async with self._client:
                if self._button_def.type == const.CodeTypes.IRCODE:
                    for _ in range(1, self._button_def.repeat + 1):
                        await self._client.send_ircode(
                            self._button_def.code, wait_for_reply=self._button_def.wait
                        )
                if self._button_def.type == const.CodeTypes.TELEPORT:
                    for _ in range(1, self._button_def.repeat + 1):
                        await self._client.send_teleport(self._button_def.code)
        except Exception as exc:
            _LOG.error("%s", exc)
            err = True
        # endregion

        if err:
            return ucapi.StatusCodes.SERVER_ERROR

        return ucapi.StatusCodes.OK

    @property
    def ucapi_entity(self) -> ucapi.Button:
        """Return the ucapi button"""
        return self._ucapi_entity
