#!/usr/bin/env python3
"""This module implements a Remote Two integration driver for Android TV devices."""

import asyncio
import logging
import os
from typing import Any

import config
import remote
import ucapi
from const import POLLER_FUNCS, PollerType
from decorators import attaches_to
from logger import log, log_formatter
from setup_flow import SetupFlow

_BACKGROUND_POLLERS: dict[str, asyncio.Task] = {}
_LOG: logging.Logger = logging.getLogger("driver")
_LOG_INC_DATETIME: bool = True
try:
    _LOOP: asyncio.AbstractEventLoop = asyncio.get_running_loop()
except RuntimeError:
    _LOOP: asyncio.AbstractEventLoop = asyncio.new_event_loop()

_configured_tivos: dict[str, remote.TivoRemote] = {}

api = ucapi.IntegrationAPI(_LOOP)


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
def _configure_new_device(device_config: config.VmTivoDevice) -> None:
    """Create and configure a new device, creating and registering the entities."""

    if device_config.id in _configured_tivos:
        _LOG.info(
            log_formatter(
                f"{device_config.id} already configured",
                include_datetime=_LOG_INC_DATETIME,
            )
        )
    else:
        device: remote.TivoRemote = remote.TivoRemote(device_config)
        device.events.on(
            remote.Events.STATE_CHANGED,
            async_on_remote_attributes_changed,
        )
        _configured_tivos[device_config.id] = device

    api.available_entities.add(device)


@api.listens_to(ucapi.Events.CONNECT)
@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_remote_connect():
    """Process a connection from the remote.

    We don't hold a connection to a device so just fake being connected.
    """
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    await async_start_poller(PollerType.STATUS)


@api.listens_to(ucapi.Events.DISCONNECT)
@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_remote_disconnect():
    """Process remote disconnect."""
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)
    await async_stop_poller(PollerType.STATUS)


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_subscribe_entities(entity_ids: list[str]) -> None:
    """"""
    for entity_id in entity_ids:
        device_id: str | None
        if (device_id := config.device_id_from_entity_id(entity_id)) is not None:
            if device_id in _configured_tivos:
                cur_state: remote.States = await _configured_tivos[
                    device_id
                ].get_state()
                await async_on_remote_attributes_changed(
                    entity_id, {ucapi.remote.Attributes.STATE: cur_state}
                )


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """Entity is no longer used in the remote."""
    for entity_id in entity_ids:
        device_id: str | None
        if (device_id := config.device_id_from_entity_id(entity_id)) is not None:
            if device_id in _configured_tivos:
                _LOG.debug(
                    log_formatter(
                        f"removing subscription for {entity_id}",
                        include_datetime=_LOG_INC_DATETIME,
                    )
                )
                _: remote.TivoRemote = _configured_tivos.pop(device_id)


@api.listens_to(ucapi.Events.ENTER_STANDBY)
@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_remote_enter_standby() -> None:
    """"""
    await async_stop_poller(PollerType.STATUS)


@api.listens_to(ucapi.Events.EXIT_STANDBY)
@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_remote_exit_standby() -> None:
    """"""
    await async_start_poller(PollerType.STATUS)


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
def on_device_added(device_config: config.VmTivoDevice) -> None:
    """Device has been added to the configuration."""
    _configure_new_device(device_config)


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
def on_device_removed(device_config: config.VmTivoDevice) -> None:
    """Device has been removed from the configuration."""

    if device_config is None:
        _LOG.debug(
            log_formatter("all devices removed", include_datetime=_LOG_INC_DATETIME)
        )
        api.configured_entities.clear()
        api.available_entities.clear()
    else:
        _LOG.debug(
            log_formatter("single device removed", include_datetime=_LOG_INC_DATETIME)
        )
        if device_config.id in _configured_tivos:
            api.configured_entities.remove(_configured_tivos[device_config.id].id)
            api.available_entities.remove(_configured_tivos[device_config.id].id)


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_on_remote_attributes_changed(
    entity_id: str, attributes: dict[str, Any]
):
    """"""

    entity: ucapi.Entity | None = None
    if (entity := api.configured_entities.get(entity_id)) is not None:
        api.configured_entities.update_attributes(entity.id, attributes)


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
@attaches_to(PollerType.STATUS)
async def async_status_poller(interval: float) -> None:
    """"""

    try:
        while True:
            for _, device in _configured_tivos.items():
                cur_state: remote.States = await device.get_state()
                await async_on_remote_attributes_changed(
                    device.id, {ucapi.remote.Attributes.STATE: cur_state}
                )
            await asyncio.sleep(interval)

    except asyncio.CancelledError as exc:
        _LOG.debug(
            log_formatter(
                f"status poller got cancelled: {exc}",
                include_datetime=_LOG_INC_DATETIME,
            )
        )
        _: asyncio.Task | None = _BACKGROUND_POLLERS.pop(PollerType.STATUS, None)
        raise


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_start_poller(task_type: PollerType, interval: float = 10.0) -> None:
    """"""

    if task_type not in _BACKGROUND_POLLERS and task_type in POLLER_FUNCS:
        polling_task: asyncio.Task = asyncio.create_task(
            POLLER_FUNCS[task_type](interval)
        )
        _BACKGROUND_POLLERS[task_type] = polling_task


@log(_LOG, include_datetime=_LOG_INC_DATETIME)
async def async_stop_poller(task_type: PollerType) -> None:
    """"""

    if (task := _BACKGROUND_POLLERS.get(task_type)) is not None:
        task.cancel("remote went into standby")


async def async_main():
    """Start the driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("button").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("setup_flow").setLevel(level)
    logging.getLogger("pyvmtivo").setLevel(level)

    config.devices = config.Devices(
        api.config_dir_path, on_device_added, on_device_removed
    )
    for device in config.devices.all():
        _configure_new_device(device)

    setup: SetupFlow = SetupFlow()
    await api.init(
        "manifest.json",
        setup.async_setup_handler,
    )


if __name__ == "__main__":
    _LOOP.run_until_complete(async_main())
    _LOOP.run_forever()
