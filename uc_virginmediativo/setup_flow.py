"""Handle the setup flow for the integration."""

import logging
import uuid
from ucapi import (
    AbortDriverSetup,
    DriverSetupRequest,
    IntegrationSetupError,
    RequestUserInput,
    SetupAction,
    SetupComplete,
    SetupDriver,
    SetupError,
    UserDataResponse,
)

import config
import discover
from pyvmtivo.client import Client, DEFAULT_CONNECT_PORT
from pyvmtivo.exceptions import VirginMediaError

_LOG = logging.getLogger(__name__)


class SetupFlow:
    """Manage the setup."""

    def __init__(self):
        """Initialise"""
        _LOG.debug("initialising SetupFlow")
        self._discovered_devices: list[dict[str, str]] = []
        self._first_step: str = "init"
        self._step_id: str
        self.rewind()

    def rewind(self) -> None:
        """Reset the current step to the first one"""
        self._step_id = self._first_step

    async def async_setup_handler(self, msg: SetupDriver) -> SetupAction:
        """Manage the steps of the setup flow."""
        _LOG.debug("setup handler: %s", msg)

        if isinstance(msg, DriverSetupRequest):
            self.rewind()

        if isinstance(msg, UserDataResponse):
            _LOG.debug("UserDataResponse: %s", msg)

            if self._step_id == self._first_step:
                self._step_id = (
                    "connect" if msg.input_values.get("address", None) else "discovery"
                )
            elif self._step_id == "discovery":
                self._step_id = "connect"

        if isinstance(msg, AbortDriverSetup):
            _LOG.debug("setup aborted (%s)", msg.error)

        if isinstance(msg, (DriverSetupRequest, UserDataResponse)):
            if (func := getattr(self, f"async_step_{self._step_id}", None)) is not None:
                _LOG.debug("moving to step: %s", self._step_id)
                return await func(msg)

            _LOG.debug("invalid setup step (%s)", self._step_id)

        return SetupError()

    async def async_step_init(
        self, msg: DriverSetupRequest
    ) -> RequestUserInput | SetupError:
        """Init step"""

        _LOG.debug("step init: %s", msg)
        return RequestUserInput(
            {
                "en": "Setup mode",
            },
            [
                {
                    "field": {
                        "text": {
                            "value": "",
                        }
                    },
                    "id": "address",
                    "label": {
                        "en": "IP address",
                    },
                },
                {
                    "id": "info",
                    "label": {
                        "en": "",
                    },
                    "field": {
                        "label": {
                            "value": {
                                "en": "Leave blank to attempt to discover devices on the network.",
                            }
                        }
                    },
                },
            ],
        )

    async def async_step_discovery(
        self, msg: DriverSetupRequest
    ) -> RequestUserInput | SetupError:
        """Discovery step"""

        _LOG.debug("step discovery: %s", msg)
        self._discovered_devices = await discover.devices()

        self._discovered_devices.append(
            {
                "address": "192.168.1.238",
                "name": "Lounge2",
                "port": 31339,
                "serial": "C68000022CD7571",
            }
        )

        if len(self._discovered_devices) == 0:
            return await self.async_step_no_devices(msg)
        if len(self._discovered_devices) == 1:
            return await self.async_step_connect(msg)
        return await self.async_step_multiple_devices(msg)

    async def async_step_multiple_devices(
        self,
        msg: UserDataResponse,
    ) -> RequestUserInput | SetupError:
        """Prompt for device to configure."""

        _LOG.debug("step multiple devices found: %s", msg)

        selections: list[dict] = [
            {
                "id": dev.get("address"),
                "label": {
                    "en": f"{dev.get('name')} [{dev.get('address')}]",
                },
            }
            for dev in self._discovered_devices
        ]
        return RequestUserInput(
            {
                "en": "Multiple devices found.",
            },
            [
                {
                    "field": {
                        "dropdown": {
                            "value": selections[0]["id"],
                            "items": selections,
                        }
                    },
                    "id": "device",
                    "label": {
                        "en": "Select your device",
                    },
                }
            ],
        )

    async def async_step_no_devices(
        self,
        msg: UserDataResponse,
    ) -> RequestUserInput | SetupError:
        """Handle no devices."""
        _LOG.debug("step no devices: %s", msg)
        return SetupError(error_type=IntegrationSetupError.NOT_FOUND)

    async def async_step_connect(
        self,
        msg: UserDataResponse,
    ) -> RequestUserInput | SetupError:
        """Connect and store devices."""

        _LOG.debug("step connect: %s", msg)
        _devices: list[dict[str, str]] = []
        if self._discovered_devices:
            _LOG.debug("from discovery")
            # only a single selection allowed so get it from the discovered devices
            selected_device: dict[str, str] = next(
                (
                    item
                    for item in self._discovered_devices
                    if item.get("address") == msg.input_values.get("device")
                ),
                None,
            )
            if selected_device is not None:
                _devices.append(selected_device)
        else:
            _LOG.debug("from user input")
            _devices = [
                {
                    "address": msg.input_values.get("address"),
                    "port": DEFAULT_CONNECT_PORT,
                }
            ]

        device: dict[str, str] = {}
        err: bool = False
        for device in _devices:
            try:
                client: Client = Client(device.get("address"), device.get("port"))
                await client.connect()
                await client.disconnect()
                tivo_device: config.VmTivoDevice = config.VmTivoDevice(
                    address=device.get("address"),
                    id=uuid.uuid4().hex,
                    name=f"{device.get('name', '')} TiVo",
                    port=device.get("port"),
                    serial=device.get("serial"),
                )
                config.devices.add(tivo_device)
                config.devices.save()
                _LOG.info(
                    "successfully configured device %s on port %s",
                    device.get("address"),
                    device.get("port"),
                )
            except Exception as exc:
                _LOG.error(
                    "error connecting to %s on port %s (%s)",
                    device.get("address"),
                    device.get("port"),
                    exc,
                )
                err = True

        if err:
            return SetupError(IntegrationSetupError.NOT_FOUND)

        return SetupComplete()
