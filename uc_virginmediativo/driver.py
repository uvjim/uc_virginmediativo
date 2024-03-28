#!/usr/bin/env python3
"""This module implements a Remote Two integration driver for Android TV devices."""

import asyncio
import logging
import os
from typing import Any
import ucapi

import button
import config
import const
import media_player
from pyvmtivo.client import Client
from setup_flow import SetupFlow

_LOG = logging.getLogger("driver")
_LOOP = asyncio.new_event_loop()
_configured_tivos: dict[str, list[button.TivoButton | media_player.TivoMediaPlayer]] = (
    {}
)

api = ucapi.IntegrationAPI(_LOOP)


def _add_configured_device(device: config.VmTivoDevice) -> None:
    """Ensure the device is available."""
    _LOG.debug("_add_configured_device: entered (%s)", device)
    _client: Client = Client(
        host=device.address, port=device.port, command_timeout=0.75
    )
    _make_available: list[button.TivoButton | media_player.TivoMediaPlayer] = []

    _make_available.append(media_player.TivoMediaPlayer(device, _client))
    _make_available[-1].events.on(
        media_player.Events.STATE_CHANGED,
        async_on_media_player_attributes_changed,
    )

    _configured_tivos[device.id] = _make_available

    for entity in _configured_tivos[device.id]:
        if api.available_entities.contains(entity.ucapi_entity.id):
            api.available_entities.remove(entity.ucapi_entity.id)
        api.available_entities.add(entity.ucapi_entity)

    _LOG.debug("_add_configured_device: exited (%s)", device)


def on_device_added(device: config.VmTivoDevice) -> None:
    """Process new device in the configuration."""
    _LOG.debug("on_device_added: entered (%s)", device)
    _add_configured_device(device)
    _LOG.debug("on_device_added: exited (%s)", device)


def on_device_removed(device: config.VmTivoDevice | None) -> None:
    """Process a removed device."""
    _LOG.debug("on_device_removed: entered")
    if device is None:
        _LOG.debug("all devices removed")
        api.configured_entities.clear()
        api.available_entities.clear()
    else:
        _LOG.debug("single device removed")
        if device.id in _configured_tivos:
            api.configured_entities.remove(device.id)
            api.available_entities.remove(device.id)
    _LOG.debug("on_device_removed: exited")


@api.listens_to(ucapi.Events.CONNECT)
async def async_on_connect():
    """Process remote connection."""
    _LOG.debug("async_on_connect: entered")
    for dev_id in _configured_tivos.keys():
        for tivo in _configured_tivos[dev_id]:
            if isinstance(tivo, media_player.TivoMediaPlayer):
                await tivo.async_query_state()

    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    _LOG.debug("async_on_connect: exited")


@api.listens_to(ucapi.Events.DISCONNECT)
async def async_on_disconnect():
    """Process remote disconnect."""
    _LOG.debug("async_on_disconnect: entered")

    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)
    _LOG.debug("async_on_disconnect: exited")


async def async_on_media_player_attributes_changed(
    entity_id: str, attributes: dict[str, Any]
):
    """Update the attributes for the media_player entity if they change."""
    _LOG.debug(
        "async_on_media_player_attributes_changed: entered (%s: %s)",
        entity_id,
        attributes,
    )
    api.configured_entities.update_attributes(entity_id, attributes)
    _LOG.debug(
        "async_on_media_player_attributes_changed: exited (%s: %s)",
        entity_id,
        attributes,
    )


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def async_on_subscribe_entities(entity_ids: list[str]) -> None:
    """"""
    _LOG.debug("async_on_subscribe_entities: entered (%s)", entity_ids)
    _LOG.debug("async_on_subscribe_entities: exited (%s)", entity_ids)


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def async_on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """"""
    _LOG.debug("async_on_unsubscribe_entities: entered (%s)", entity_ids)
    _LOG.debug("async_on_unsubscribe_entities: exited (%s)", entity_ids)


async def async_main():
    """Start the driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("button").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("setup_flow").setLevel(level)
    logging.getLogger("pyvmtivo").setLevel(level)

    config.devices = config.Devices(
        api.config_dir_path, on_device_added, on_device_removed
    )
    for device in config.devices.all():
        _add_configured_device(device)

    setup: SetupFlow = SetupFlow()
    await api.init(
        "manifest.json",
        setup.async_setup_handler,
    )


if __name__ == "__main__":
    _LOOP.run_until_complete(async_main())
    _LOOP.run_forever()
