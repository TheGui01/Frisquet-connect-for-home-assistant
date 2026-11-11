"""Entité Calendrier pour l'intégration Frisquet Connect.

Expose la programmation hebdomadaire de la chaudière sous forme d'entités
Calendar natives. La carte Calendrier de Home Assistant affiche alors les
7 jours avec les plages de chauffe (frise).

Format attendu du coordinator :
    coordinator.data[idx]["programmation"] = [
        {"jour": 0=dimanche, 1..6=lundi..samedi, "plages": [0/1, ...]},
        ...
    ]
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Créer une entité calendrier par zone."""
    _LOGGER.debug("In calendar.py async_setup_entry")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.data.setdefault("timezone", hass.config.time_zone)

    entitylist = []
    for idx in ("zone1", "zone2", "zone3"):
        if idx in coordinator.data:
            # Deux entités par zone : une par état, pour pouvoir les colorer
            # séparément (rouge = Confort, bleu = Réduit) dans HA.
            entitylist.append(
                FrisquetCalendar(
                    entry, coordinator, idx, coordinator.data.get("nomInstall"),
                    filter_value=1,
                )
            )
            entitylist.append(
                FrisquetCalendar(
                    entry, coordinator, idx, coordinator.data.get("nomInstall"),
                    filter_value=0,
                )
            )
    async_add_entities(entitylist, update_before_add=False)


class FrisquetCalendar(CoordinatorEntity, CalendarEntity):
    """Calendrier de chauffe d'une zone (lecture seule)."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: CoordinatorEntity,
        idx: str,
        site: str | None,
        filter_value: int | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.idx = idx
        self.site = site
        self.coordinator = coordinator
        self.tz = coordinator.data.get("timezone", "Europe/Paris")
        # None = tous les états ; 1 = Confort seul ; 0 = Réduit seul
        self.filter_value = filter_value

        self.IDChaudiere = coordinator.data[idx]["identifiant_chaudiere"]
        suffix = {None: "", 1: "Confort", 0: "Reduit"}[filter_value]
        self._attr_unique_id = "CAL" + suffix + self.IDChaudiere + str(
            coordinator.data[idx].get("numero", "")
        )
        zone_label = idx.replace("zone", "Zone ")
        self._attr_name = (
            f"Programmation {zone_label} {suffix}" if suffix else f"Programmation {zone_label}"
        )
        self._attr_has_entity_name = True
        self._attr_supported_features = 0  # lecture seule : pas d'ajout d'events

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.IDChaudiere)},
            name=self.site,
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx].get("produit"),
            serial_number=self.IDChaudiere,
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Événement en cours, s'il y en a un."""
        now = datetime.now(ZoneInfo(self.tz))
        for ev in self._events_for_range(now.replace(hour=0, minute=0, second=0, microsecond=0), now + timedelta(days=1)):
            if ev.start <= now <= ev.end:
                return ev
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Événements entre deux dates (générés à partir du programme hebdo)."""
        return self._events_for_range(start_date, end_date)

    # ------------------------------------------------------------------
    # Génération des événements
    # ------------------------------------------------------------------

    def _events_for_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Convertit le programme hebdomadaire en événements datés."""
        tz = ZoneInfo(self.tz)
        prog = self.coordinator.data.get(self.idx, {}).get("programmation", [])
        if not prog:
            return []

        # Générer toutes les semaines chevauchant la plage demandée
        events: list[CalendarEvent] = []
        week_start = self._monday_of(start_date.astimezone(tz))
        while week_start < end_date:
            events.extend(self._week_to_events(prog, week_start, tz))
            week_start += timedelta(days=7)

        # Dédupliquer (les plages fusionnées à cheval sur 2 semaines
        # sont régénérées à l'itération suivante) et filtrer
        seen = set()
        result = []
        for ev in events:
            key = (ev.start.isoformat(), ev.end.isoformat(), ev.summary)
            if key in seen:
                continue
            seen.add(key)
            if ev.end > start_date and ev.start < end_date:
                result.append(ev)
        result.sort(key=lambda ev: ev.start)
        return result

    def _week_to_events(
        self, prog: list[dict], week_start: datetime, tz: ZoneInfo
    ) -> list[CalendarEvent]:
        """Convertit une semaine complète en événements Confort / Réduit.

        Les tranches contiguës de même état sont fusionnées, y compris
        à cheval sur minuit (ex. Réduit de 23:00 à 05:59 le lendemain).
        """
        if not prog:
            return []

        plages_ref = next((j.get("plages", []) for j in prog if j.get("plages")), [])
        if not plages_ref:
            return []
        step_min = 5 if len(plages_ref) >= 288 else 30
        slots_per_day = len(plages_ref)

        # Aplatir la semaine : une valeur par tranche, index 0 = lundi
        # Numérotation Frisquet : jour 0 = dimanche, 1..6 = lundi..samedi
        semaine: list[int] = []
        by_day = {int(j["jour"]) % 7: j.get("plages", []) for j in prog}
        for weekday in range(7):  # 0 = lundi ... 6 = dimanche
            jour_frisquet = (weekday + 1) % 7
            semaine.extend(by_day.get(jour_frisquet, [0] * slots_per_day))

        # Détecter les plages contiguës de même état
        runs: list[tuple[int, int, int]] = []  # (start_slot, end_slot, value)
        start = 0
        for i in range(1, len(semaine) + 1):
            if i == len(semaine) or semaine[i] != semaine[start]:
                runs.append((start, i, semaine[start]))
                start = i

        # Fusionner la dernière plage avec la première si même état
        # (ex. Réduit dimanche 23:00 -> lundi 05:59)
        if len(runs) > 1 and runs[0][2] == runs[-1][2] and runs[0][0] == 0 and runs[-1][1] == len(semaine):
            first_start, _, value = runs.pop(0)
            last_start, _, _ = runs.pop()
            runs.append((last_start, len(semaine) + first_start, value))

        events = []
        for run_start, run_end, value in runs:
            if self.filter_value is not None and value != self.filter_value:
                continue
            summary = "Confort" if value == 1 else "Réduit"
            events.append(
                CalendarEvent(
                    start=week_start + timedelta(minutes=run_start * step_min),
                    end=week_start + timedelta(minutes=run_end * step_min),
                    summary=summary,
                    description=f"Programmation {summary.lower()}",
                )
            )
        return events

    def _monday_of(self, dt: datetime) -> datetime:
        """Minuit du lundi de la semaine de dt."""
        monday = (dt - timedelta(days=dt.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return monday

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
