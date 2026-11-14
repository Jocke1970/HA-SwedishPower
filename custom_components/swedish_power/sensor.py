"""Swedish national power sensors, based on source-timestamped reports."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SOURCE
from .coordinator import SwedishPowerCoordinator
from .reactor_coordinator import ReactorSourceCoordinator
from .vattenfall import VATTENFALL_REACTORS, VattenfallSnapshot
from .okg import OkgO3Reading, OKG_URL

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
    """Expose eight national and six independent reactor MW sensors."""
    runtime = entry.runtime_data
    entities = [SwedishPowerSensor(runtime.statnett, description) for description in DESCRIPTIONS]
    for plant, source in runtime.reactors.items():
        for reactor in VATTENFALL_REACTORS.get(plant, ("O3",)):
            entities.append(SwedishReactorPowerSensor(source, reactor))
    async_add_entities(entities)


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


REACTOR_TRANSLATIONS = {
    "F1": "reactor_f1",
    "F2": "reactor_f2",
    "F3": "reactor_f3",
    "R3": "reactor_r3",
    "R4": "reactor_r4",
    "O3": "reactor_o3",
}
REACTOR_PLANT_NAMES = {"forsmark": "Forsmark", "ringhals": "Ringhals", "oskarshamn": "Oskarshamn"}


class SwedishReactorPowerSensor(CoordinatorEntity[ReactorSourceCoordinator], SensorEntity):
    """One source-observed reactor MW output; never infer operating status."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "MW"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: ReactorSourceCoordinator, reactor_id: str) -> None:
        super().__init__(coordinator)
        self._reactor_id = reactor_id
        self.entity_description = SensorEntityDescription(
            key=REACTOR_TRANSLATIONS[reactor_id],
            translation_key=REACTOR_TRANSLATIONS[reactor_id],
        )
        self._attr_unique_id = f"{DOMAIN}_se_reactor_{reactor_id.casefold()}_mw"
        plant = coordinator.plant
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"reactors_{plant}")},
            name=f"Swedish Power {REACTOR_PLANT_NAMES[plant]}",
            manufacturer="Vattenfall (data source)" if plant != "oskarshamn"
            else "OKG (data source)",
            model="Source-reported reactor electrical power",
        )

    @property
    def _reading(self):
        snapshot = self.coordinator.data
        if isinstance(snapshot, VattenfallSnapshot):
            return snapshot.reactors.get(self._reactor_id)
        if isinstance(snapshot, OkgO3Reading) and self._reactor_id == "O3":
            return snapshot
        return None

    @property
    def available(self) -> bool:
        reading = self._reading
        return super().available and reading is not None and reading.quality == "valid"

    @property
    def native_value(self) -> float | None:
        if not self.available:
            return None
        reading = self._reading
        return reading.power_mw if isinstance(self.coordinator.data, VattenfallSnapshot) else reading.value_mw

    @property
    def extra_state_attributes(self) -> dict:
        reading = self._reading
        if reading is None:
            return {
                "reactor_id": self._reactor_id,
                "source": "Vattenfall" if self.coordinator.plant != "oskarshamn" else "OKG",
                "quality": "source_unavailable",
                "status_interpretation": "not inferred from power",
            }
        snapshot = self.coordinator.data
        attrs = {
            "reactor_id": self._reactor_id,
            "plant": self.coordinator.plant,
            "source": "Vattenfall" if self.coordinator.plant != "oskarshamn" else "OKG",
            "source_url": snapshot.source_url if isinstance(snapshot, VattenfallSnapshot) else OKG_URL,
            "source_measured_at": reading.measured_at.isoformat() if reading.measured_at else None,
            "fetched_at": snapshot.fetched_at.isoformat(),
            "quality": reading.quality,
            "data_kind": "operator-reported reactor output",
            "status_interpretation": "not inferred from power",
        }
        if isinstance(snapshot, VattenfallSnapshot):
            attrs.update({
                "source_snapshot_at": snapshot.measured_at.isoformat() if snapshot.measured_at else None,
                "source_unit": reading.source_unit,
                "source_reported_percent": reading.reported_percent,
                "timestamp_basis": "operator_snapshot",
            })
        else:
            attrs.update({
                "source_snapshot_at": reading.api_timestamp.isoformat() if reading.api_timestamp else None,
                "timestamp_basis": reading.timestamp_basis,
                "source_unit": "MW",
                "source_unit_basis": reading.source_unit_basis,
            })
        return attrs
