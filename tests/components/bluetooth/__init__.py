"""Tests for the Bluetooth integration."""


import time
from typing import Any
from unittest.mock import patch

from bleak.backends.scanner import AdvertisementData, BLEDevice
from bluetooth_adapters import DEFAULT_ADDRESS

from homeassistant.components.bluetooth import (
    DOMAIN,
    SOURCE_LOCAL,
    async_get_advertisement_callback,
    models,
)
from homeassistant.components.bluetooth.manager import BluetoothManager
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry

__all__ = (
    "inject_advertisement",
    "inject_advertisement_with_source",
    "inject_advertisement_with_time_and_source",
    "inject_advertisement_with_time_and_source_connectable",
    "inject_bluetooth_service_info",
    "patch_all_discovered_devices",
    "patch_discovered_devices",
    "generate_advertisement_data",
)

ADVERTISEMENT_DATA_DEFAULTS = {
    "local_name": "",
    "manufacturer_data": {},
    "service_data": {},
    "service_uuids": [],
    "rssi": -127,
    "platform_data": ((),),
    "tx_power": -127,
}


def generate_advertisement_data(**kwargs: Any) -> AdvertisementData:
    """Generate advertisement data with defaults."""
    new = kwargs.copy()
    for key, value in ADVERTISEMENT_DATA_DEFAULTS.items():
        new.setdefault(key, value)
    return AdvertisementData(**new)


def _get_manager() -> BluetoothManager:
    """Return the bluetooth manager."""
    return models.MANAGER


def inject_advertisement(
    hass: HomeAssistant, device: BLEDevice, adv: AdvertisementData
) -> None:
    """Inject an advertisement into the manager."""
    return inject_advertisement_with_source(hass, device, adv, SOURCE_LOCAL)


def inject_advertisement_with_source(
    hass: HomeAssistant, device: BLEDevice, adv: AdvertisementData, source: str
) -> None:
    """Inject an advertisement into the manager from a specific source."""
    inject_advertisement_with_time_and_source(
        hass, device, adv, time.monotonic(), source
    )


def inject_advertisement_with_time_and_source(
    hass: HomeAssistant,
    device: BLEDevice,
    adv: AdvertisementData,
    time: float,
    source: str,
) -> None:
    """Inject an advertisement into the manager from a specific source at a time."""
    inject_advertisement_with_time_and_source_connectable(
        hass, device, adv, time, source, True
    )


def inject_advertisement_with_time_and_source_connectable(
    hass: HomeAssistant,
    device: BLEDevice,
    adv: AdvertisementData,
    time: float,
    source: str,
    connectable: bool,
) -> None:
    """Inject an advertisement into the manager from a specific source at a time and connectable status."""
    async_get_advertisement_callback(hass)(
        models.BluetoothServiceInfoBleak(
            name=adv.local_name or device.name or device.address,
            address=device.address,
            rssi=adv.rssi,
            manufacturer_data=adv.manufacturer_data,
            service_data=adv.service_data,
            service_uuids=adv.service_uuids,
            source=source,
            device=device,
            advertisement=adv,
            connectable=connectable,
            time=time,
        )
    )


def inject_bluetooth_service_info_bleak(
    hass: HomeAssistant, info: models.BluetoothServiceInfoBleak
) -> None:
    """Inject an advertisement into the manager with connectable status."""
    advertisement_data = generate_advertisement_data(
        local_name=None if info.name == "" else info.name,
        manufacturer_data=info.manufacturer_data,
        service_data=info.service_data,
        service_uuids=info.service_uuids,
        rssi=info.rssi,
    )
    device = BLEDevice(  # type: ignore[no-untyped-call]
        address=info.address,
        name=info.name,
        details={},
    )
    inject_advertisement_with_time_and_source_connectable(
        hass,
        device,
        advertisement_data,
        info.time,
        SOURCE_LOCAL,
        connectable=info.connectable,
    )


def inject_bluetooth_service_info(
    hass: HomeAssistant, info: models.BluetoothServiceInfo
) -> None:
    """Inject a BluetoothServiceInfo into the manager."""
    advertisement_data = generate_advertisement_data(  # type: ignore[no-untyped-call]
        local_name=None if info.name == "" else info.name,
        manufacturer_data=info.manufacturer_data,
        service_data=info.service_data,
        service_uuids=info.service_uuids,
        rssi=info.rssi,
    )
    device = BLEDevice(  # type: ignore[no-untyped-call]
        address=info.address,
        name=info.name,
        details={},
    )
    inject_advertisement(hass, device, advertisement_data)


def patch_all_discovered_devices(mock_discovered: list[BLEDevice]) -> None:
    """Mock all the discovered devices from all the scanners."""
    return patch.object(
        _get_manager(),
        "_async_all_discovered_addresses",
        return_value={ble_device.address for ble_device in mock_discovered},
    )


def patch_discovered_devices(mock_discovered: list[BLEDevice]) -> None:
    """Mock the combined best path to discovered devices from all the scanners."""
    return patch.object(
        _get_manager(), "async_discovered_devices", return_value=mock_discovered
    )


async def async_setup_with_default_adapter(hass: HomeAssistant) -> MockConfigEntry:
    """Set up the Bluetooth integration with a default adapter."""
    return await _async_setup_with_adapter(hass, DEFAULT_ADDRESS)


async def async_setup_with_one_adapter(hass: HomeAssistant) -> MockConfigEntry:
    """Set up the Bluetooth integration with one adapter."""
    return await _async_setup_with_adapter(hass, "00:00:00:00:00:01")


async def _async_setup_with_adapter(
    hass: HomeAssistant, address: str
) -> MockConfigEntry:
    """Set up the Bluetooth integration with any adapter."""
    entry = MockConfigEntry(domain="bluetooth", unique_id=address)
    entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    return entry
