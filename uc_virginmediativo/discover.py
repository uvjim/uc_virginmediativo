"""Discover the Virgin Media TiVo devices on the network."""

import asyncio
import logging

from zeroconf import ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

_LOG = logging.getLogger(__name__)


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

        _LOG.info("found service: %s, %s", service_type, name)
        _ = asyncio.ensure_future(display_service_info(zeroconf, service_type, name))

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
                _LOG.debug("found: %s", discovered_device)
                discovered_devices.append(discovered_device)
        else:
            _LOG.debug("no info for %s", name)

    try:
        _LOG.debug("discovering devices")
        aiozc = AsyncZeroconf()
        services = ["_tivo-remote._tcp.local."]

        aiobrowser = AsyncServiceBrowser(
            aiozc.zeroconf, services, handlers=[on_service_state_changed]
        )

        await asyncio.sleep(timeout)
        await aiobrowser.async_cancel()
        await aiozc.async_close()
        _LOG.debug("discovery finished")
    except OSError as err:
        _LOG.error("failed starting discovery: %s", err)

    return discovered_devices
