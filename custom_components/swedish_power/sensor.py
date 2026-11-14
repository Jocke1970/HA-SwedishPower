"""Swedish national power sensors, based on source-timestamped reports."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCE
from .coordinator import SwedishPowerCoordinator

DESCRIPTIONS = (
    SensorEntityDescription(key="production", translation_key="production"),
    SensorEntityDescription(key="consumption", translation_key="consumption"),
    SensorEntityDescription(key="net_exchange", translation_key="net_exchange"),
    SensorEntityDescription(key="hydro", translation_key="hydro"),
    SensorEntityDescription(key="wind", translation_key="wind"),
    SensorEntityDescription(key="nuclear", translation_key="nuclear"),
    SensorEntityDescription(key="thermal", translation_key="thermal"),
    SensorEntityDescription(key="other", translation_key="other"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Expose only the eight verified national fields."""
    coordinator: SwedishPowerCoordinator = entry.runtime_data
    async_add_entities(
        SwedishPowerSensor(coordinator, description) for description in DESCRIPTIONS
    )


class SwedishPowerSensor(CoordinatorEntity[SwedishPowerCoordinator], SensorEntity):
    """An individual, source-aware national MW sensor."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "MW"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: SwedishPowerCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_se_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "sweden")},
            name="Swedish Power Sweden",
            manufacturer="Statnett (data source)",
            model="Swedish national electricity overview",
        )

    @property
    def available(self) -> bool:
        """Do not report stale, invalid or missing data as current."""
        if not super().available or not self.coordinator.data:
            return False
        reading = self.coordinator.data.production.readings.get(self.entity_description.key)
        return reading is not None and reading.quality == "valid"

    @property
    def native_value(self) -> float | None:
        """Provide MW only when the source record is current and valid."""
        if not self.available:
            return None
        return self.coordinator.data.production.readings[self.entity_description.key].value_mw

    @property
    def extra_state_attributes(self) -> dict:
        """Surface measurement-vs-retrieval time and provenance."""
        if not self.coordinator.data:
            return {}
        snapshot = self.coordinator.data.production
        reading = snapshot.readings.get(self.entity_description.key)
        if reading is None:
            return {}
        return {
            "source": SOURCE,
            "scope": "SE",
            "quality": reading.quality,
            "timestamp_basis": reading.timestamp_basis,
            "source_measured_at": reading.measured_at.isoformat() if reading.measured_at else None,
            "source_snapshot_at": snapshot.snapshot_at.isoformat() if snapshot.snapshot_at else None,
            "fetched_at": snapshot.fetched_at.isoformat(),
            "period_start_label": reading.period_start_label,
            "period_end_label": reading.period_end_label,
            "data_kind": "source_reported; actual/forecast mix not independently verified",
        }
