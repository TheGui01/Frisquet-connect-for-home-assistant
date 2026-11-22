"""Plages Hors gel programmées dans Home Assistant.

La programmation de la chaudière ne connaît que Confort (1) et Réduit (0) ;
le Hors gel est un mode (SELECTEUR_Zx = 8). Les plages Hors gel sont donc
gardées par Home Assistant, au même format que la programmation
(7 jours x 48 créneaux de 30 min, jour 0 = dimanche), et appliquées en
basculant le mode :

- au début d'une période Hors gel : SELECTEUR = 8, sauf si la zone est déjà
  en Hors gel ou en vacances ;
- à la fin : retour en automatique (SELECTEUR = 5), seulement si c'est
  l'intégration qui avait mis le Hors gel et que la zone y est toujours.

Seuls le début et la fin d'une période déclenchent un ordre : un mode
choisi à la main pendant la période est respecté. Sur ces créneaux, la
programmation de la chaudière reste en Réduit, ce qui sert de repli si
Home Assistant est arrêté.
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .service import async_send_order

_LOGGER = logging.getLogger(__name__)

ZONES = ("zone1", "zone2", "zone3")
SELECTEUR_AUTO = 5
SELECTEUR_HORS_GEL = 8


def _vide() -> list[list[int]]:
    return [[0] * 48 for _ in range(7)]


class FrisquetHorsGel:
    """Plages Hors gel d'une entrée de configuration."""

    def __init__(self, hass: HomeAssistant, entry, coordinator) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._store = Store(hass, 1, f"{DOMAIN}.hors_gel.{entry.entry_id}")
        # zone -> {"plages": [[48 x 0/1] x 7], "periode": bool, "actif": bool}
        self._zones: dict[str, dict] = {}
        self._unsub = None

    async def async_start(self) -> None:
        stored = await self._store.async_load() or {}
        for zone_key in ZONES:
            if zone_key in (self.coordinator.data or {}):
                zone = stored.get(zone_key) or {}
                plages = zone.get("plages")
                if not (isinstance(plages, list) and len(plages) == 7):
                    plages = _vide()
                self._zones[zone_key] = {
                    "plages": plages,
                    "periode": bool(zone.get("periode")),
                    "actif": bool(zone.get("actif")),
                }
        self._unsub = async_track_time_change(
            self.hass, self._async_tick, minute=(0, 30), second=5
        )
        # Rattraper une bascule manquée pendant un arrêt de Home Assistant.
        self.hass.async_create_task(self.async_evaluate())

    @callback
    def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    def programmation(self, zone_key: str) -> list[dict] | None:
        """Plages au format de l'attribut programmation (None si inconnue)."""
        zone = self._zones.get(zone_key)
        if zone is None:
            return None
        return [{"jour": jour, "plages": list(p)} for jour, p in enumerate(zone["plages"])]

    async def async_set(self, zone_key: str, programmation: list[dict]) -> None:
        zone = self._zones.setdefault(
            zone_key, {"plages": _vide(), "periode": False, "actif": False}
        )
        plages = _vide()
        for jour in programmation:
            valeurs = [1 if int(v) == 1 else 0 for v in jour["plages"]][:48]
            plages[int(jour["jour"]) % 7] = valeurs + [0] * (48 - len(valeurs))
        zone["plages"] = plages
        await self._async_save()
        self.coordinator.async_update_listeners()
        await self.async_evaluate()

    async def _async_save(self) -> None:
        await self._store.async_save(self._zones)

    async def _async_tick(self, _now) -> None:
        await self.async_evaluate()

    async def async_evaluate(self) -> None:
        now = dt_util.now()
        jour = (now.weekday() + 1) % 7  # Frisquet : 0 = dimanche
        creneau = (now.hour * 60 + now.minute) // 30
        changed = False

        for zone_key, zone in self._zones.items():
            data = (self.coordinator.data or {}).get(zone_key)
            if not data:
                continue
            hors_gel = zone["plages"][jour][creneau] == 1
            selecteur = data.get("SELECTEUR")

            if hors_gel and not zone["periode"]:
                zone["periode"] = True
                vacances = (self.coordinator.data.get("vacances") or {}).get("MODE_VACANCES")
                if selecteur != SELECTEUR_HORS_GEL and not vacances:
                    zone["actif"] = await self._async_selecteur(zone_key, SELECTEUR_HORS_GEL)
                else:
                    zone["actif"] = False
                changed = True

            elif not hors_gel and zone["periode"]:
                zone["periode"] = False
                if zone["actif"] and selecteur == SELECTEUR_HORS_GEL:
                    await self._async_selecteur(zone_key, SELECTEUR_AUTO)
                zone["actif"] = False
                changed = True

        if changed:
            await self._async_save()

    async def _async_selecteur(self, zone_key: str, valeur: int) -> bool:
        data = self.coordinator.data[zone_key]
        order = [{"cle": f"SELECTEUR_Z{data['numero']}", "valeur": str(valeur)}]
        try:
            await async_send_order(self.hass, self.entry, self.coordinator, zone_key, order)
        except Exception as err:  # noqa: BLE001 - on réessaiera à la prochaine période
            _LOGGER.error("Hors gel : échec de l'ordre %s : %s", order, err)
            return False

        _LOGGER.info("Hors gel : %s passe en SELECTEUR %s", zone_key, valeur)
        valeurs = {"SELECTEUR": valeur, "DERO": False}
        if valeur == SELECTEUR_HORS_GEL:
            valeurs["MODE"] = SELECTEUR_HORS_GEL
        api = getattr(self.coordinator, "frisquet_api", None)
        for key, value in valeurs.items():
            data[key] = value
            if api is not None:
                api.set_cached_value(zone_key, key, value)
        self.coordinator.async_update_listeners()
        return True
