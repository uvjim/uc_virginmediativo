"""Handle configuration for the driver."""

import dataclasses
import json
import logging
import os
from typing import Callable, Iterator

from logger import log, log_formatter

_LOG = logging.getLogger(__name__)
_LOG_INC_DATETIME: bool = True


@dataclasses.dataclass
class VmTivoDevice:
    """Virgin Media TiVo device."""

    address: str
    id: str
    name: str
    port: int
    serial: str


class _CustomJSONEncoder(json.JSONEncoder):
    """Encoder for VmTivoDevice."""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


AddCallback = Callable[[VmTivoDevice], None]
RemoveCallback = Callable[[VmTivoDevice | None], None]


def device_id_from_entity_id(entity_id: str) -> str | None:
    """"""
    return entity_id.split(".")[1]


class Devices:
    """Manage all configured devices."""

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def __init__(
        self,
        config_dir: str,
        add_callback: AddCallback | None = None,
        remove_callback: RemoveCallback | None = None,
    ) -> None:
        """Initialise."""

        self._callback_add: AddCallback | None = add_callback
        self._callback_remove: RemoveCallback | None = remove_callback
        self._config_dir: str = config_dir
        self._config_path: str = os.path.join(self._config_dir, "config.json")
        self._config: list[VmTivoDevice] = []
        self.load()

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def add(self, tivo: VmTivoDevice) -> None:
        """Add a new device as configured."""
        if not self.contains(tivo.address):
            self._config.append(tivo)
            if self._callback_add is not None:
                self._callback_add(tivo)
        else:
            _LOG.debug("device already exists - %s", tivo.name)

    def all(self) -> Iterator[VmTivoDevice]:
        """Allow iterating over configured devices."""
        return iter(self._config)

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def clear(self) -> None:
        """Clear all configured devices."""
        self._config = []
        if self._callback_remove is not None:
            self._callback_remove(None)

    def contains(self, address: str) -> bool:
        """Check if device exits by address."""
        ret = False
        for itm in self._config:
            if itm.address == address:
                ret = True
                break

        return ret

    def get(self, tivo_id: str) -> VmTivoDevice | None:
        """Retrieve a device from the configured devices."""
        for itm in self._config:
            if itm.id == tivo_id:
                return dataclasses.replace(itm)

        return None

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def load(self) -> bool:
        """Load the configured devices from disk."""
        ret = False

        try:
            if not os.path.exists(self._config_path):
                _LOG.debug(
                    log_formatter(
                        "no configuration file found",
                        include_datetime=_LOG_INC_DATETIME,
                    )
                )
            else:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for itm in data:
                    self._config.append(VmTivoDevice(**itm))
            ret = True
        except OSError:
            _LOG.error("error opening the config file")
        except ValueError:
            _LOG.error("invalid config file")

        return ret

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def remove(self, tivo_id: str) -> bool:
        """Remove a device from the configuration."""
        tivo_device: VmTivoDevice | None
        ret: bool = False

        if (tivo_device := self.get(tivo_id)) is not None:
            try:
                self._config.remove(tivo_device)
                if self._callback_remove is not None:
                    self._callback_remove(tivo_device)
                ret = True
            except ValueError:
                pass

        return ret

    @log(_LOG, include_datetime=_LOG_INC_DATETIME)
    def save(self) -> bool:
        """Save configured devices to disk."""
        ret: bool = False

        try:
            with open(self._config_path, "w+", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, cls=_CustomJSONEncoder)
            ret = True
        except OSError:
            _LOG.error("error writing config file")

        return ret

    @property
    def data_path(self) -> str:
        """Return the configuration directory."""
        return self._config_dir


devices: Devices | None = None
