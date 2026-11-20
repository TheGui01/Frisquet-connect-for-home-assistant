/**
 * Frisquet Schedule Card — frise hebdomadaire interactive.
 *
 * Lecture : plages Confort / Réduit de l'attribut `programmation`
 * de l'entité climate (jour 0 = dimanche ... 6 = samedi, 48 créneaux de 30 min).
 *
 * Édition : bouton « Modifier » -> clic pour basculer un créneau,
 * glissement pour peindre, « Enregistrer » -> appelle le service
 * (par défaut frisquet_connect.set_programmation) qui envoie
 * l'ordre PROGRAMME_{zone} à l'API Frisquet.
 *
 * Configuration :
 *   entity: climate.xxx                     (obligatoire)
 *   service: frisquet_connect.set_programmation (optionnel)
 *   title / confort_color / reduit_color    (optionnel)
 */

const DEFAULT_CONFORT_COLOR = "#ff5252";
const DEFAULT_REDUIT_COLOR = "#42a5f5";

const DAY_NAMES = {
  0: "Dimanche",
  1: "Lundi",
  2: "Mardi",
  3: "Mercredi",
  4: "Jeudi",
  5: "Vendredi",
  6: "Samedi",
};

const DISPLAY_DAYS = [1, 2, 3, 4, 5, 6, 0];

const CARD_STYLES = `
  :host {
  --frisquet-confort-color: #ff5252;
  --frisquet-reduit-color: #42a5f5;
  }

  ha-card {
    padding: 16px;
  }

  .title {
    font-size: 1.1em;
    font-weight: 600;
    margin-bottom: 12px;
  }

  .warn {
    color: var(--error-color, red);
    padding: 12px;
    overflow-wrap: anywhere;
  }

  .day {
    width: 82px;
    flex: none;
    font-size: 0.85em;
    color: var(--primary-text-color);
  }

  .day.today {
    font-weight: 700;
    color: var(--accent-color, orange);
  }

  .track-bg {
    position: absolute;
    inset: 0;
    border-radius: 6px;
    background: var(--frisquet-reduit-color);
    opacity: 0.35;
  }

  .slot,
  .blk {
    position: absolute;
    top: 0;
    height: 100%;
    border-radius: 4px;
  }

  .slot.confort,
  .blk.confort {
    background: var(--frisquet-confort-color);
  }

  .slot.reduit,
  .blk.reduit {
    background: transparent;
    z-index: 1;
  }

  .chg {
    position: absolute;
    top: -12px;
    width: 0;
    z-index: 2;
  }

  .chg::before {
    content: "";
    position: absolute;
    left: -1px;
    top: 2px;
    width: 2px;
    height: 20px;
    background: var(--primary-text-color, #333);
    opacity: 0.55;
    border-radius: 1px;
  }

  .chg span {
    position: absolute;
    top: -11px;
    left: 0;
    transform: translateX(-50%);
    white-space: nowrap;
    font-size: 0.62em;
    color: var(--secondary-text-color);
  }

  .tooltip {
    position: fixed;
    z-index: 999;
    pointer-events: none;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color, #111);
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 0.8em;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    display: none;
  }

  .scale {
    position: relative;
    height: 18px;
    margin-left: 82px;
  }

  .tick {
    position: absolute;
    transform: translateX(-50%);
    font-size: 0.7em;
    color: var(--secondary-text-color);
  }

  .legend {
    display: flex;
    gap: 16px;
    margin-top: 10px;
    font-size: 0.85em;
    color: var(--primary-text-color);
  }

  .edit-ranges {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    margin: -2px 0 8px 82px;
    font-size: 0.72em;
    color: var(--secondary-text-color);
  }
  .row {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    min-width: 0;
  }

  .track {
    position: relative;
    flex: 1 1 0%;
    min-width: 0;
    height: 22px;
    margin-top: 12px;
  }

  .track.editable {
    cursor: crosshair;
    touch-action: none;
    user-select: none;
    -webkit-user-select: none;
  }
  .range {
    white-space: nowrap;
  }

  .range::before {
    content: "";
    display: inline-block;
    width: 7px;
    height: 7px;
    margin-right: 4px;
    border-radius: 50%;
    vertical-align: 1px;
  }

  .range.confort::before {
    background: var(--frisquet-confort-color);
  }

  .range.reduit::before {
    background: var(--frisquet-reduit-color);
  }

  .dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
  }

  .dot.confort {
    background: var(--frisquet-confort-color);
  }

  .dot.reduit {
    background: var(--frisquet-reduit-color);
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 14px;
    flex-wrap: wrap;
  }

  .btn {
    border: 1px solid var(--divider-color, #ccc);
    border-radius: 18px;
    background: var(--card-background-color, #fff);
    color: var(--primary-text-color);
    padding: 6px 18px;
    font-size: 0.9em;
    cursor: pointer;
  }

  .btn:hover:not(:disabled) {
    filter: brightness(0.9);
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .hint {
    font-size: 0.75em;
    color: var(--secondary-text-color);
  }

  .status {
    font-size: 0.85em;
    overflow-wrap: anywhere;
  }

  .status.ok {
    color: var(--primary-text-color);
  }

  .status.err {
    color: var(--error-color, red);
  }
`;

function isValidColor(value) {
  if (typeof value !== "string" || value.trim() === "") {
    return false;
  }

  try {
    return CSS.supports("color", value.trim());
  } catch (_) {
    return false;
  }
}

function safeColor(value, fallback) {
  return isValidColor(value) ? value.trim() : fallback;
}

function formatTime(minutes) {
  const hours = Math.floor(minutes / 60) % 24;
  const mins = minutes % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);

  if (className) {
    element.className = className;
  }

  if (text !== undefined && text !== null) {
    element.textContent = String(text);
  }

  return element;
}

class FrisquetScheduleCard extends HTMLElement {
  setConfig(config) {
    if (!config || typeof config !== "object") {
      throw new Error("Configuration de la carte invalide.");
    }

    if (!config.entity || typeof config.entity !== "string") {
      throw new Error("Vous devez définir une entité.");
    }

    this.config = config;
    this._hass = null;
    this._editMode = false;
    this._edit = null;
    this._saving = false;
    this._status = null;
    this._optimistic = null;
    this._painting = false;
    this._paintValue = null;
    this._renderRoot = this.attachShadow({ mode: "open" });

    this._render();
  }

  set hass(hass) {
    this._hass = hass;

    // Ne pas reconstruire la carte pendant un glissement :
    // cela détruirait la piste en cours d'édition.
    if (this._painting) {
      return;
    }

    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getStubConfig() {
    return { entity: "" };
  }

  // ---------------------------------------------------------------- helpers

  _render() {
    try {
      this._renderInner();
    } catch (error) {
      this._renderError(
        `Erreur carte : ${error instanceof Error ? error.message : String(error)}`
      );
      console.error("frisquet-schedule-card :", error);
    }
  }

  _renderError(message) {
    const card = createElement("ha-card");
    const warning = createElement("div", "warn", message);

    card.appendChild(warning);
    this._replaceChildren(card);
  }

  _replaceChildren(...children) {
    const root = this._renderRoot;
    root.replaceChildren();

    const style = document.createElement("style");
    style.textContent = CARD_STYLES;
    root.appendChild(style);

    for (const child of children) {
      root.appendChild(child);
    }
  }

  _getEntity() {
    return this._hass ? this._hass.states[this.config.entity] : null;
  }

  _sameProg(first, second) {
    return JSON.stringify(first) === JSON.stringify(second);
  }

  _initEditBuffer(programmation) {
    const days = Array.from({ length: 7 }, () => new Array(48).fill(0));

    if (Array.isArray(programmation)) {
      for (const day of programmation) {
        const dayIndex = ((Number(day.jour) % 7) + 7) % 7;
        const ranges = Array.isArray(day.plages) ? day.plages : [];
        const rangeCount = ranges.length;

        if (rangeCount === 0) {
          continue;
        }

        // Normalisation en 48 créneaux (si la source est plus fine, ex. 288 x 5 min).
        for (let slot = 0; slot < 48; slot++) {
          const from = Math.round((slot * rangeCount) / 48);
          const to = Math.max(
            from,
            Math.round(((slot + 1) * rangeCount) / 48)
          );

          let comfortSlots = 0;
          let seenSlots = 0;

          for (let index = from; index < to && index < rangeCount; index++) {
            comfortSlots += Number(ranges[index]) === 1 ? 1 : 0;
            seenSlots++;
          }

          days[dayIndex][slot] =
            seenSlots > 0 && comfortSlots * 2 > seenSlots ? 1 : 0;
        }
      }
    }

    this._edit = { data: days, dirty: false };
  }

  // ---------------------------------------------------------------- rendu

  _renderInner() {
    if (!this.config || !this._hass) {
      return;
    }

    const stateObject = this._getEntity();

    if (!stateObject) {
      this._renderError(`Entité introuvable : ${this.config.entity}`);
      return;
    }

    let programmation = stateObject.attributes?.programmation;

    // Affichage optimiste : tant que l'entité n'a pas rattrapé la programmation
    // envoyée, on affiche ce qui a été envoyé.
    if (this._optimistic) {
      if (this._sameProg(programmation, this._optimistic)) {
        this._optimistic = null;
      } else {
        programmation = this._optimistic;
      }
    }

    if (!this._editMode && (!Array.isArray(programmation) || !programmation.length)) {
      this._renderError(
        `Attribut « programmation » absent de ${this.config.entity}`
      );
      return;
    }

    const card = createElement("ha-card");
    const confortColor = safeColor(
      this.config.confort_color,
      DEFAULT_CONFORT_COLOR
    );
    const reduitColor = safeColor(
      this.config.reduit_color,
      DEFAULT_REDUIT_COLOR
    );

    card.style.setProperty("--frisquet-confort-color", confortColor);
    card.style.setProperty("--frisquet-reduit-color", reduitColor);
    if (this.config.title) {
      card.appendChild(
        createElement("div", "title", this.config.title)
      );
    }

    const rows = createElement("div", "rows");
    const nowDay = new Date().getDay();
    const rawSlotCount = Math.max(
      ...(programmation || []).map(
        (day) => (Array.isArray(day.plages) ? day.plages : []).length
      ),
      0
    );
    const stepMinutes = rawSlotCount >= 288 ? 5 : 30;

    for (const dayIndex of DISPLAY_DAYS) {
      rows.appendChild(
        this._createDayRow(
          dayIndex,
          nowDay === dayIndex,
          programmation,
          stepMinutes
        )
      );
    }

    card.appendChild(rows);
    card.appendChild(this._createScale());
    card.appendChild(this._createLegend());
    card.appendChild(this._createActions());

    const tooltip = createElement("div", "tooltip");
    card.appendChild(tooltip);

    this._replaceChildren(card);
    this._wireEvents(tooltip);
  }

  _createDayRow(dayIndex, isToday, programmation, stepMinutes) {
    const row = createElement("div", "row");
    const dayLabel = createElement(
      "div",
      isToday ? "day today" : "day",
      DAY_NAMES[dayIndex]
    );

    const track = createElement(
      "div",
      this._editMode ? "track editable" : "track"
    );
    track.dataset.day = String(dayIndex);

    track.appendChild(createElement("div", "track-bg"));

    let ranges;

    if (this._editMode) {
      ranges = this._edit.data[dayIndex];
    } else {
      const day = (programmation || []).find(
        (item) => ((Number(item.jour) % 7) + 7) % 7 === dayIndex
      );
      ranges = Array.isArray(day?.plages) ? day.plages : [];
    }

    const total = ranges.length || 48;
    const intervalStepMinutes = this._editMode ? 30 : stepMinutes;
    const editRanges = this._editMode
      ? createElement("div", "edit-ranges")
      : null;

    let index = 0;
    let lastChangePosition = -100;

    while (index < ranges.length) {
      const value = Number(ranges[index]) === 1 ? 1 : 0;
      let end = index;

      while (
        end < ranges.length &&
        (Number(ranges[end]) === 1 ? 1 : 0) === value
      ) {
        end++;
      }

      const left = (index / total) * 100;
      const width = ((end - index) / total) * 100;
      const startTime = formatTime(index * intervalStepMinutes);
      const endTime =
        end >= total ? "24:00" : formatTime(end * intervalStepMinutes);
      const stateName = value === 1 ? "Confort" : "Réduit";
      const stateClass = value === 1 ? "confort" : "reduit";

      if (this._editMode) {
        const range = createElement(
          "span",
          `range ${stateClass}`,
          `${stateName} ${startTime}–${endTime}`
        );
        editRanges.appendChild(range);

        const slot = createElement("div", `slot ${stateClass}`);
        slot.dataset.day = String(dayIndex);
        slot.dataset.index = String(index);
        slot.style.left = `${left}%`;
        slot.style.width = `${width}%`;
        track.appendChild(slot);
      } else {
        const block = createElement("div", `blk ${stateClass}`);
        block.dataset.tip = `${DAY_NAMES[dayIndex]} : ${stateName} ${startTime} – ${endTime}`;
        block.style.left = `${left}%`;
        block.style.width = `${width}%`;
        track.appendChild(block);

        if (index > 0 && left - lastChangePosition > 5) {
          const change = createElement("div", "chg");
          const changeLabel = createElement(
            "span",
            null,
            formatTime(index * intervalStepMinutes)
          );

          change.style.left = `${left}%`;
          change.appendChild(changeLabel);
          track.appendChild(change);
          lastChangePosition = left;
        }
      }

      index = end;
    }

    row.appendChild(dayLabel);
    row.appendChild(track);

    // La liste des plages doit être sous la ligne,
    // et non dans le même conteneur flex que la piste.
    const fragment = document.createDocumentFragment();
    fragment.appendChild(row);

    if (editRanges) {
      fragment.appendChild(editRanges);
    }

    return fragment;
  }

  _createScale() {
    const scale = createElement("div", "scale");

    for (let hour = 0; hour <= 24; hour += 3) {
      const tick = createElement(
        "div",
        "tick",
        String(hour).padStart(2, "0")
      );
      tick.style.left = `${(hour / 24) * 100}%`;
      scale.appendChild(tick);
    }

    return scale;
  }

  _createLegend() {
    const legend = createElement("div", "legend");

    const confort = createElement("span");
    const confortDot = createElement("span", "dot confort");
    confort.appendChild(confortDot);
    confort.appendChild(document.createTextNode("Confort"));

    const reduit = createElement("span");
    const reduitDot = createElement("span", "dot reduit");
    reduit.appendChild(reduitDot);
    reduit.appendChild(document.createTextNode("Réduit"));

    legend.appendChild(confort);
    legend.appendChild(reduit);

    return legend;
  }

  _createActions() {
    const actions = createElement("div", "actions");

    if (this._editMode) {
      const saveButton = createElement(
        "button",
        "btn save",
        this._saving ? "Envoi…" : "Enregistrer"
      );
      saveButton.id = "btn-save";
      saveButton.type = "button";
      saveButton.disabled = this._saving || !this._edit?.dirty;

      const cancelButton = createElement("button", "btn cancel", "Annuler");
      cancelButton.id = "btn-cancel";
      cancelButton.type = "button";

      const hint = createElement(
        "span",
        "hint",
        "Cliquez pour basculer un créneau · glissez pour peindre (30 min)"
      );

      actions.appendChild(saveButton);
      actions.appendChild(cancelButton);
      actions.appendChild(hint);
    } else {
      const editButton = createElement("button", "btn edit", "Modifier");
      editButton.id = "btn-edit";
      editButton.type = "button";
      actions.appendChild(editButton);
    }

    if (this._status) {
      actions.appendChild(
        createElement(
          "div",
          `status ${this._status.ok ? "ok" : "err"}`,
          this._status.text
        )
      );
    }

    return actions;
  }

  // ---------------------------------------------------------------- events

  _wireEvents(tooltip) {
    const root = this._renderRoot;

    root.querySelectorAll(".blk").forEach((block) => {
      block.addEventListener("mouseenter", () => {
        tooltip.textContent = block.dataset.tip || "";
        tooltip.style.display = "block";
      });

      block.addEventListener("mousemove", (event) => {
        tooltip.style.left = `${event.clientX + 12}px`;
        tooltip.style.top = `${event.clientY + 12}px`;
      });

      block.addEventListener("mouseleave", () => {
        tooltip.style.display = "none";
      });
    });

    const editButton = root.querySelector("#btn-edit");

    if (editButton) {
      editButton.addEventListener("click", () => {
        const stateObject = this._getEntity();
        const programmation =
          this._optimistic || stateObject?.attributes?.programmation;

        this._initEditBuffer(programmation);
        this._editMode = true;
        this._status = null;
        this._painting = false;
        this._paintValue = null;
        this._render();
      });
    }

    const cancelButton = root.querySelector("#btn-cancel");

    if (cancelButton) {
      cancelButton.addEventListener("click", () => {
        this._editMode = false;
        this._saving = false;
        this._status = null;
        this._painting = false;
        this._paintValue = null;
        this._render();
      });
    }

    const saveButton = root.querySelector("#btn-save");

    if (saveButton) {
      saveButton.addEventListener("click", () => {
        this._save();
      });
    }

    if (!this._editMode) {
      return;
    }

    root.querySelectorAll(".track.editable").forEach((track) => {
      track.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        this._painting = true;
        this._paintValue = null;

        try {
          track.setPointerCapture(event.pointerId);
        } catch (_) {
          // Le navigateur peut refuser le pointer capture.
        }

        this._paintSlot(track, event);
      });

      track.addEventListener("pointermove", (event) => {
        if (!this._painting) {
          return;
        }

        this._paintSlot(track, event);
      });

      const stopPainting = () => {
        if (!this._painting) {
          return;
        }

        this._painting = false;
        this._paintValue = null;
        this._render();
      };

      track.addEventListener("pointerup", stopPainting);
      track.addEventListener("pointercancel", stopPainting);
      track.addEventListener("lostpointercapture", stopPainting);
    });
  }

  _paintSlot(track, event) {
    if (!this._edit) {
      return;
    }

    const day = Number(track.dataset.day);

    if (!Number.isInteger(day) || day < 0 || day > 6) {
      return;
    }

    const rect = track.getBoundingClientRect();

    if (!rect.width) {
      return;
    }

    const ratio = Math.min(
      0.9999,
      Math.max(0, (event.clientX - rect.left) / rect.width)
    );
    const index = Math.floor(ratio * 48);

    if (index < 0 || index > 47) {
      return;
    }

    if (this._paintValue === null) {
      this._paintValue = this._edit.data[day][index] === 1 ? 0 : 1;
    }

    if (this._edit.data[day][index] !== this._paintValue) {
      this._edit.data[day][index] = this._paintValue;
      this._edit.dirty = true;
      this._updateTrackVisual(track, day);
    }
  }

  _updateTrackVisual(track, day) {
    if (!this._edit) {
      return;
    }

    const ranges = this._edit.data[day];
    const fragment = document.createDocumentFragment();

    fragment.appendChild(createElement("div", "track-bg"));

    let index = 0;

    while (index < ranges.length) {
      const value = Number(ranges[index]) === 1 ? 1 : 0;
      let end = index;

      while (
        end < ranges.length &&
        (Number(ranges[end]) === 1 ? 1 : 0) === value
      ) {
        end++;
      }

      const slot = createElement(
        "div",
        `slot ${value === 1 ? "confort" : "reduit"}`
      );

      slot.dataset.day = String(day);
      slot.dataset.index = String(index);
      slot.style.left = `${(index / 48) * 100}%`;
      slot.style.width = `${((end - index) / 48) * 100}%`;

      fragment.appendChild(slot);
      index = end;
    }

    track.replaceChildren(fragment);
  }

  _paintSlot(track, event) {
    const day = Number(track.dataset.day);

    if (!Number.isInteger(day) || day < 0 || day > 6 || !this._edit) {
      return;
    }

    const rect = track.getBoundingClientRect();
    const ratio = Math.min(
      0.9999,
      Math.max(0, (event.clientX - rect.left) / rect.width)
    );
    const index = Math.floor(ratio * 48);

    if (index < 0 || index > 47) {
      return;
    }

    if (this._paintValue === null) {
      this._paintValue = this._edit.data[day][index] === 1 ? 0 : 1;
    }

    if (this._edit.data[day][index] !== this._paintValue) {
      this._edit.data[day][index] = this._paintValue;
      this._edit.dirty = true;
      this._updateTrackVisual(track, day);
    }
  }

  // Rafraîchit la piste éditée sans tout réafficher, pour rester fluide.
  _updateTrackVisual(track, day) {
    const ranges = this._edit.data[day];
    track.replaceChildren(createElement("div", "track-bg"));

    let index = 0;

    while (index < ranges.length) {
      const value = Number(ranges[index]) === 1 ? 1 : 0;
      let end = index;

      while (
        end < ranges.length &&
        (Number(ranges[end]) === 1 ? 1 : 0) === value
      ) {
        end++;
      }

      const slot = createElement(
        "div",
        `slot ${value === 1 ? "confort" : "reduit"}`
      );
      slot.dataset.day = String(day);
      slot.dataset.index = String(index);
      slot.style.left = `${(index / 48) * 100}%`;
      slot.style.width = `${((end - index) / 48) * 100}%`;

      track.appendChild(slot);
      index = end;
    }
  }

  // ---------------------------------------------------------------- envoi

  async _save() {
    if (!this._hass || !this._edit || this._saving) {
      return;
    }

    this._saving = true;
    this._status = { ok: true, text: "Envoi en cours…" };
    this._render();

    const programmation = this._edit.data.map((ranges, day) => ({
      jour: day,
      plages: ranges.slice(),
    }));

    const service = this.config.service || "frisquet_connect.set_programmation";
    const [domain, serviceName] = service.split(".");

    try {
      await this._hass.callService(
        domain || "frisquet_connect",
        serviceName || "set_programmation",
        {
          entity_id: this.config.entity,
          programmation,
        }
      );

      this._status = {
        ok: true,
        text: "Programmation envoyée à la chaudière",
      };
      this._optimistic = programmation;
      this._editMode = false;
      this._edit = null;
    } catch (error) {
      this._status = {
        ok: false,
        text: `Échec : ${error instanceof Error ? error.message : String(error)
          }`,
      };
      this._editMode = false;
      this._edit = null;
    }

    this._saving = false;
    this._render();
  }
}

if (!customElements.get("frisquet-schedule-card")) {
  customElements.define("frisquet-schedule-card", FrisquetScheduleCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "frisquet-schedule-card",
  name: "Frisquet Schedule Card",
  description:
    "Frise hebdomadaire interactive de la programmation Frisquet (Confort / Réduit)",
});

console.info(
  "frisquet-schedule-card loaded from Frisquet Connect integration"
);