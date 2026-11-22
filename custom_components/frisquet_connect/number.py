"""Consignes Confort / Réduit / Hors gel de chaque zone.

L'entité climate ne modifie que la consigne du mode en cours. Ces entités
number permettent de régler les trois consignes indépendamment du mode
(ordres CONS_CONF_Zx, CONS_RED_Zx, CONS_HG_Zx, en dixièmes de degré).
"""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .service import async_send_order

_LOGGER = logging.getLogger(__name__)

# (clé Frisquet, libellé, icône)
CONSIGNES = (
    ("CONS_CONF", "Confort", "mdi:sun-thermometer-outline"),
    ("CONS_RED", "Réduit", "mdi:weather-night"),
    ("CONS_HG", "Hors gel", "mdi:snowflake-thermometer"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Créer les trois consignes de chaque zone."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        FrisquetConsigne(entry, coordinator, idx, key, label, icon)
        for idx in ("zone1", "zone2", "zone3")
        if idx in coordinator.data
        for key, label, icon in CONSIGNES
        if coordinator.data[idx].get(key) is not None
    ]
    async_add_entities(entities, update_before_add=False)


class FrisquetConsigne(CoordinatorEntity, NumberEntity):
    """Consigne de température d'un mode pour une zone."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 5
    _attr_native_max_value = 30
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, entry, coordinator, idx: str, key: str, label: str, icon: str) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.idx = idx
        self.key = key
        zone = coordinator.data[idx]
        self.IDChaudiere = str(zone["identifiant_chaudiere"])
        self._attr_unique_id = f"{key}{self.IDChaudiere}{zone.get('numero', '')}"
        zone_label = idx.replace("zone", "Zone ")
        self._attr_name = f"Consigne {zone_label} {label}"
        self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.IDChaudiere)},
            name=self.coordinator.data.get("nomInstall"),
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx].get("produit"),
            serial_number=self.IDChaudiere,
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.idx, {}).get(self.key)
        return None if value is None else value / 10

    async def async_set_native_value(self, value: float) -> None:
        zone = self.coordinator.data[self.idx]
        dixiemes = int(round(value * 10))
        order = [{
            "cle": f"{self.key}_Z{zone['numero']}",
            "valeur": str(dixiemes),
        }]
        await async_send_order(self.hass, self.entry, self.coordinator, self.idx, order)

        # L'API met la valeur à jour tout de suite : on l'applique localement
        # (et dans le cache de l'API) pour que climate et number la reflètent.
        zone[self.key] = dixiemes
        api = getattr(self.coordinator, "frisquet_api", None)
        if api is not None:
            api.set_cached_value(self.idx, self.key, dixiemes)
        self.coordinator.async_update_listeners()
