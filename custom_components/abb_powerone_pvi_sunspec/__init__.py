"""The ABB Power-One PVI SunSpec Integration"""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)

from .api import ABBPowerOnePVISunSpecHub
from .const import (CONF_BASE_ADDR, CONF_HOST, CONF_NAME, CONF_PORT,
                    CONF_SCAN_INTERVAL, CONF_SLAVE_ID, DOMAIN, PLATFORMS,
                    STARTUP_MESSAGE)

_LOGGER: logging.Logger = logging.getLogger(__package__)

SCAN_INTERVAL = timedelta(seconds=60)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up this integration using UI"""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    name = config_entry.data.get(CONF_NAME)
    host = config_entry.data.get(CONF_HOST)
    port = config_entry.data.get(CONF_PORT)
    slave_id = config_entry.data.get(CONF_SLAVE_ID)
    base_addr = config_entry.data.get(CONF_BASE_ADDR)
    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL)

    hub = ABBPowerOnePVISunSpecHub(hass, name, host, port, slave_id, base_addr, scan_interval)

    _LOGGER.debug("Setup config entry for ABB")
    hass.data[DOMAIN][config_entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS):
        hass.data[DOMAIN].pop(config_entry.entry_id)
        _LOGGER.debug("async_unload_entry: ok")
    else:
        _LOGGER.debug("async_unload_entry: failed")
    return unload_ok

class HubDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, hub: ABBPowerOnePVISunSpecHub, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.hub = hub
        self.config_entry = config_entry

        _LOGGER.debug("Data: %s", self.config_entry.data)
        _LOGGER.debug("Options: %s", self.config_entry.options)

        scan_interval = timedelta(
            seconds=self.config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self.config_entry.data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL.total_seconds()),
            )
        )

        _LOGGER.debug(
            "Setup entry with scan interval %s. Host: %s Port: %s ID: %s Base Addr.: %s",
            scan_interval,
            self.config_entry.data.get(CONF_HOST),
            self.config_entry.data.get(CONF_PORT),
            self.config_entry.data.get(CONF_SLAVE_ID),
            self.config_entry.data.get(CONF_BASE_ADDR),
        )
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=scan_interval)

    async def _async_update_data(self):
        """Update data via library."""
        _LOGGER.debug("ABB SunSpec Update data coordinator update")
        try:
            data = await self.hub.async_get_data()
            return data
        except Exception as exception:
            _LOGGER.debug(f"Async Update Data error: {exception}")
            raise UpdateFailed() from exception


# async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
#     """Migrate an old config entry."""
#     version = config_entry.version

#     # 1-> 2: Migration format
#     if version == 1:
#         hub_name = config_entry.data.get(CONF_NAME)
#         hub = hass.data[DOMAIN][hub_name]["hub"]
#         # hub.read_sunspec_modbus_init()
#         # hub.read_sunspec_modbus_data()
#         _LOGGER.debug("Migrating from version %s", version)
#         old_uid = config_entry.unique_id
#         new_uid = hub.data["comm_sernum"]
#         if old_uid != new_uid:
#             hass.config_entries.async_update_entry(
#                 entry, unique_id=new_uid
#             )
#             _LOGGER.debug("Migration to version %s complete: OLD_UID: %s - NEW_UID: %s", config_entry.version, old_uid, new_uid)
#         if config_entry.unique_id == new_uid:
#             config_entry.version = 2
#             _LOGGER.debug("Migration to version %s complete: NEW_UID: %s", config_entry.version, config_entry.unique_id)
#     return True

