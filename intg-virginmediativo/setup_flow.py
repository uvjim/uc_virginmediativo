"""Handle the setup flow for the integration."""

import logging
import uuid

import config
import discover
from logger import log, log_formatter
from pyvmtivo.client import DEFAULT_CONNECT_PORT, Client
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

_LOG: logging.Logger = logging.getLogger(__name__)
_LOG_INC_DATETIME: bool = True


class SetupFlow:
    """Manage the setup."""

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def __init__(self):
        """Initialise."""
        self._discovered_devices: list[dict[str, str]] = []
        self._first_step: str = "init"
        self._step_id: str
        self.rewind()

    def rewind(self) -> None:
        """Reset the current step to the first one."""
        self._step_id = self._first_step

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_setup_handler(self, msg: SetupDriver) -> SetupAction:
        """Manage the steps of the setup flow."""

        if isinstance(msg, DriverSetupRequest):
            self.rewind()

        if isinstance(msg, UserDataResponse):
            _LOG.debug(
                log_formatter(
                    f"UserDataResponse: {msg}", include_datetime=_LOG_INC_DATETIME
                )
            )

            if self._step_id == self._first_step:
                self._step_id = (
                    "connect" if msg.input_values.get("address", None) else "discovery"
                )
            elif self._step_id == "discovery":
                self._step_id = "connect"

        if isinstance(msg, AbortDriverSetup):
            _LOG.debug(
                log_formatter(
                    f"setup aborted ({msg.error})", include_datetime=_LOG_INC_DATETIME
                )
            )

        if isinstance(msg, (DriverSetupRequest, UserDataResponse)):
            if (func := getattr(self, f"async_step_{self._step_id}", None)) is not None:
                _LOG.debug(
                    log_formatter(
                        f"moving to step: {self._step_id}",
                        include_datetime=_LOG_INC_DATETIME,
                    )
                )
                return await func(msg)

            _LOG.debug(
                log_formatter(
                    f"invalid setup step ({self._step_id})",
                    include_datetime=_LOG_INC_DATETIME,
                )
            )

        return SetupError()

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_step_init(
        self, msg: DriverSetupRequest
    ) -> RequestUserInput | SetupError:
        """Init step."""

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

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_step_discovery(
        self, msg: DriverSetupRequest
    ) -> RequestUserInput | SetupError:
        """Discovery step."""

        self._discovered_devices = await discover.devices()

        if len(self._discovered_devices) == 0:
            return await self.async_step_no_devices(msg)
        if len(self._discovered_devices) == 1:
            return await self.async_step_connect(msg)
        return await self.async_step_multiple_devices(msg)

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_step_multiple_devices(
        self,
        msg: UserDataResponse,
    ) -> RequestUserInput | SetupError:
        """Prompt for device to configure."""

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

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_step_no_devices(
        self,
        msg: UserDataResponse,
    ) -> RequestUserInput | SetupError:
        """Handle no devices."""
        return SetupError(error_type=IntegrationSetupError.NOT_FOUND)

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    async def async_step_connect(
        self,
        msg: UserDataResponse,
    ) -> RequestUserInput | SetupError:
        """Connect and store devices."""

        _devices: list[dict[str, str]] = []
        if self._discovered_devices:
            _LOG.debug(
                log_formatter("from discovery", include_datetime=_LOG_INC_DATETIME)
            )
            _LOG.debug(
                log_formatter(
                    f"discovered_devices: {self._discovered_devices}",
                    include_datetime=_LOG_INC_DATETIME,
                )
            )

            if len(self._discovered_devices) == 1:
                selected_device = self._discovered_devices[0]
            elif len(self._discovered_devices) > 1:
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
            _LOG.debug(
                log_formatter("from user input", include_datetime=_LOG_INC_DATETIME)
            )
            _devices = [
                {
                    "address": msg.input_values.get("address"),
                    "port": DEFAULT_CONNECT_PORT,
                }
            ]

        device: dict[str, str] = {}
        err: bool = False
        _LOG.debug(
            log_formatter(f"_devices: {_devices}", include_datetime=_LOG_INC_DATETIME)
        )
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
                    log_formatter(
                        f"successfully configured device {device.get('address')} on port {device.get('port')}",
                        include_datetime=_LOG_INC_DATETIME,
                    )
                )
            except Exception as exc:
                _LOG.error(
                    log_formatter(
                        f"error connecting to {device.get('address')} on port {device.get('port')} ({exc})",
                        include_datetime=_LOG_INC_DATETIME,
                    )
                )
                err = True

        if err:
            return SetupError(IntegrationSetupError.NOT_FOUND)

        return SetupComplete()
