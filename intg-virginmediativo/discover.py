"""Discover the Virgin Media TiVo devices on the network."""

import asyncio
import logging

from logger import log, log_formatter
from zeroconf import ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

_LOG: asyncio.AbstractEventLoop = logging.getLogger(__name__)
_LOG_INC_DATETIME: bool = True


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def devices(timeout: int = 10) -> list[dict[str, str]]:
    """Discover devices."""
    discovered_devices: list[dict[str, str]] = []

    def on_service_state_changed(
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        if state_change is not ServiceStateChange.Added:
            return

        _LOG.info(
            log_formatter(
                f"found service: {service_type}, {name}",
                include_datetime=_LOG_INC_DATETIME,
            )
        )
        task_service_info: asyncio.Task = asyncio.ensure_future(  # noqa: F841,RUF006
            display_service_info(zeroconf, service_type, name)
        )

    async def display_service_info(
        zeroconf: Zeroconf, service_type: str, name: str
    ) -> None:
        info = AsyncServiceInfo(service_type, name)
        await info.async_request(zeroconf, 3000)

        if info:
            addresses = info.parsed_scoped_addresses()
            if addresses:
                discovered_device = {
                    "address": addresses[0],
                    "name": name.split(".")[0],
                    "port": info.port,
                    "serial": info.properties.get(b"TSN").decode("utf-8"),
                }
                _LOG.debug(
                    log_formatter(
                        f"found: {discovered_device}",
                        include_datetime=_LOG_INC_DATETIME,
                    )
                )
                discovered_devices.append(discovered_device)
        else:
            _LOG.debug(
                log_formatter(f"no info for {name}", include_datetime=_LOG_INC_DATETIME)
            )

    try:
        aiozc = AsyncZeroconf()
        services = ["_tivo-remote._tcp.local."]

        aiobrowser = AsyncServiceBrowser(
            aiozc.zeroconf, services, handlers=[on_service_state_changed]
        )

        await asyncio.sleep(timeout)
        await aiobrowser.async_cancel()
        await aiozc.async_close()
    except OSError as err:
        _LOG.error(
            log_formatter(
                f"failed starting discovery: {err}", include_datetime=_LOG_INC_DATETIME
            )
        )

    return discovered_devices
