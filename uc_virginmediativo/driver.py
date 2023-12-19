#!/usr/bin/env python3
"""This module implements a Remote Two integration driver for Android TV devices."""

import asyncio
import logging
import os
from typing import Any
import ucapi

import config
import media_player
from pyvmtivo.client import Client
from setup_flow import SetupFlow

_LOG = logging.getLogger("driver")
_LOOP = asyncio.new_event_loop()
_configured_tivos: dict[str, media_player.TivoMediaPlayer] = {}

api = ucapi.IntegrationAPI(_LOOP)


def _add_configured_device(device: config.VmTivoDevice) -> None:
    """Ensure the device is available."""
    media_entity: media_player.TivoMediaPlayer = media_player.TivoMediaPlayer(
        device, Client(host=device.address, port=device.port, command_timeout=0.75)
    )

    _configured_tivos[device.id] = media_entity

    if api.available_entities.contains(media_entity.ucapi_mediaplayer.id):
        api.available_entities.remove(media_entity.ucapi_mediaplayer.id)
    api.available_entities.add(media_entity.ucapi_mediaplayer)


def on_device_added(device: config.VmTivoDevice) -> None:
    """Process new device in the configuration."""
    _LOG.debug("new device: %s", device)
    _add_configured_device(device)


def on_device_removed(device: config.VmTivoDevice | None) -> None:
    """Process a removed device."""
    if device is None:
        _LOG.debug("all devices removed")
        api.configured_entities.clear()
        api.available_entities.clear()
    else:
        _LOG.debug("single device removed")
        if device.id in _configured_tivos:
            api.configured_entities.remove(device.id)
            api.available_entities.remove(device.id)


@api.listens_to(ucapi.Events.CONNECT)
async def async_on_connect():
    """Process remote connection."""
    _LOG.debug("remote connected")


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def async_on_subscribe_entities(entity_ids) -> None:
    """"""
    _LOG.debug("subscribe entities event, %s", entity_ids)


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def async_on_unsubscribe_entities(entity_ids) -> None:
    """"""
    _LOG.debug("unsubscribe entities event, %s", entity_ids)


async def async_main():
    """Start the driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("config").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("setup_flow").setLevel(level)
    logging.getLogger("pyvmtivo").setLevel(level)

    config.devices = config.Devices(
        api.config_dir_path, on_device_added, on_device_removed
    )
    for device in config.devices.all():
        _LOG.debug("adding configured devices")
        _add_configured_device(device)

    setup: SetupFlow = SetupFlow()
    await api.init(
        "manifest.json",
        setup.async_setup_handler,
    )


if __name__ == "__main__":
    _LOOP.run_until_complete(async_main())
    _LOOP.run_forever()
