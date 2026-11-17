/**
 * Frisquet Schedule Card — frise hebdomadaire interactive.
 *
 * Lecture : plages Confort / Réduit de l'attribut `programmation`
 * de l'entité climate (jour 0 = dimanche ... 6 = samedi, 48 créneaux de 30 min).
 *
 * Édition : bouton "Modifier" -> clic pour basculer un créneau,
 * glissement pour peindre, "Enregistrer" -> appelle le service
 * (par défaut frisquet_connect.set_programmation) qui envoie
 * l'ordre PROGRAMME_{zone} à l'API Frisquet.
 *
 * Configuration :
 *   entity: climate.xxx                               (obligatoire)
 *   service: frisquet_connect.set_programmation       (optionnel)
 *   title / confort_color / reduit_color              (optionnel)
 */

class FrisquetScheduleCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Vous devez définir une entité");
    this.config = config;
    this._hass = null;
    this._editMode = false;
    this._edit = null;          // { data: [7][48], dirty }
    this._saving = false;
    this._status = null;        // { ok: bool, text: string }
    this._optimistic = null;    // programmation envoyée, affichée en attendant la maj
    this._painting = false;
    this._paintValue = null;
    this._renderRoot = this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // En édition : on ne réaffiche pas depuis l'entité pour ne pas
    // écraser le buffer en cours de modification.
    this._render();
  }

  getCardSize() { return 4; }

  static getStubConfig() { return { entity: "" }; }

  // ---------------------------------------------------------------- helpers

  _render() {
    try { this._renderInner(); }
    catch (e) {
      this._renderRoot.innerHTML =
        `<ha-card><div class="warn">Erreur carte : ${e.message}</div></ha-card>`;
      console.error("frisquet-schedule-card :", e);
    }
  }

  _getEntity() {
    return this._hass ? this._hass.states[this.config.entity] : null;
  }

  _sameProg(a, b) {
    return JSON.stringify(a) === JSON.stringify(b);
  }

  // Buffer d'édition : 7 jours x 48 créneaux de 30 min (jour 0 = dimanche).
  _initEditBuffer(prog) {
    const days = new Array(7);
    for (let d = 0; d < 7; d++) days[d] = new Array(48).fill(0);
    if (prog && prog.length) {
      for (const j of prog) {
        const d = ((j.jour % 7) + 7) % 7;
        const plages = j.plages || [];
        // Normalisation en 48 créneaux (si la source est plus fine, ex. 288 x 5 min).
        for (let i = 0; i < 48; i++) {
          const from = Math.round((i * plages.length) / 48);
          const to = Math.max(from, Math.round(((i + 1) * plages.length) / 48));
          let ones = 0, seen = 0;
          for (let k = from; k < to && k < plages.length; k++) { ones += plages[k]; seen++; }
          days[d][i] = seen && (ones * 2 > seen) ? 1 : 0;
        }
      }
    }
    this._edit = { data: days, dirty: false };
  }

  // ----------------------------------------------------------------  rendu

  _renderInner() {
    if (!this.config || !this._hass) return;
    const stateObj = this._getEntity();
    if (!stateObj) {
      this._renderRoot.innerHTML =
        `<ha-card><div class="warn">Entité introuvable : ${this.config.entity}</div></ha-card>`;
      return;
    }

    let prog = stateObj.attributes.programmation;

    // Affichage optimiste : tant que l'entité n'a pas rattrapé la programmation
    // envoyée, on affiche ce qu'on a envoyé.
    if (this._optimistic) {
      if (this._sameProg(prog, this._optimistic)) {
        this._optimistic = null; // l'entité est à jour
      } else {
        prog = this._optimistic;
      }
    }

    if (!this._editMode && (!prog || !prog.length)) {
      this._renderRoot.innerHTML =
        `<ha-card><div class="warn">Attribut "programmation" absent de ${this.config.entity}</div></ha-card>`;
      return;
    }

    const confortColor = this.config.confort_color || "#ff5252";
    const reduitColor = this.config.reduit_color || "#42a5f5";
    const joursFrisquet = { 0: "Dimanche", 1: "Lundi", 2: "Mardi", 3: "Mercredi", 4: "Jeudi", 5: "Vendredi", 6: "Samedi" };
    const ordreAffichage = [1, 2, 3, 4, 5, 6, 0];
    const nowDay = new Date().getDay();
    const fmtTime = (m) => `${String(Math.floor(m / 60) % 24).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;

    const totalRaw = Math.max(...(prog || []).map(j => (j.plages || []).length), 0);
    const stepMin = totalRaw >= 288 ? 5 : 30;

    let rows = "";
    for (const d of ordreAffichage) {
      const jourNom = joursFrisquet[d];
      const isToday = d === nowDay;
      let plages, editable;

      if (this._editMode) {
        plages = this._edit.data[d];
        editable = true;
      } else {
        plages = (prog.find(j => ((j.jour % 7) + 7) % 7 === d) || {}).plages || [];
        editable = false;
      }
      const total = plages.length || 48;
      const intervalStepMin = editable ? 30 : stepMin;

      let blocks = "";
      let chg = "";
      let editRanges = "";
      let lastPct = -100;
      let i = 0;
      while (i < plages.length) {
        const v = plages[i];
        let j = i;
        while (j < plages.length && plages[j] === v) j++;
        const left = (i / total) * 100;
        const width = ((j - i) / total) * 100;
        const startTime = fmtTime(i * intervalStepMin);
        const endTime = j >= total ? "24:00" : fmtTime(j * intervalStepMin);
        const label = `${startTime} – ${endTime}`;
        const etat = v === 1 ? "Confort" : "Réduit";
        if (editable) {
          editRanges += `<span class="range ${v === 1 ? "confort" : "reduit"}">
            ${etat} ${startTime}–${endTime}</span>`;
        }
        blocks += editable
          ? `<div class="slot ${v === 1 ? "confort" : "reduit"}" data-day="${d}" data-idx="${i}"
                 style="left:${left}%;width:${width}%;${v === 1 ? `background:${confortColor}` : ""}"></div>`
          : `<div class="blk ${v === 1 ? "confort" : "reduit"}" data-tip="${jourNom} : ${etat} ${label}"
                 style="left:${left}%;width:${width}%;${v === 1 ? `background:${confortColor}` : ""}"></div>`;
        // Repères horaires des changements de plage (lecture seule, hors 00:00)
        if (!editable && i > 0) {
          const pct = left;
          if (pct - lastPct > 5) {
            chg += `<div class="chg" style="left:${pct}%"><span>${fmtTime(i * intervalStepMin)}</span></div>`;
            lastPct = pct;
          }
        }
        i = j;
      }

      rows += `
        <div class="row">
          <div class="day ${isToday ? "today" : ""}">${jourNom}</div>
          <div class="track ${editable ? "editable" : ""}" data-day="${d}">
            <div class="track-bg"></div>
            ${blocks}
            ${chg}
          </div>
        </div>
        ${editable ? `<div class="edit-ranges">${editRanges}</div>` : ""}`;
    }

    let scale = "";
    for (let h = 0; h <= 24; h += 3)
      scale += `<div class="tick" style="left:${(h / 24) * 100}%">${String(h).padStart(2, "0")}</div>`;

    const statusHtml = this._status
      ? `<div class="status ${this._status.ok ? "ok" : "err"}">${this._status.text}</div>` : "";
    const actions = `
      <div class="actions">
        ${this._editMode ? `
          <button class="btn save" id="btn-save" ${this._saving || !this._edit.dirty ? "disabled" : ""}>
            ${this._saving ? "Envoi…" : "Enregistrer"}</button>
          <button class="btn cancel" id="btn-cancel">Annuler</button>
          <span class="hint">Cliquez pour basculer un créneau · glissez pour peindre (30 min)</span>
        ` : `<button class="btn edit" id="btn-edit">Modifier</button>`}
        ${statusHtml}
      </div>`;

    this._renderRoot.innerHTML = `
      <style>
        ha-card { padding: 16px; }
        .title { font-size: 1.1em; font-weight: 600; margin-bottom: 12px; }
        .warn { color: var(--error-color, red); padding: 12px; }
        .row { display: flex; align-items: center; margin-bottom: 6px; }
        .day { width: 82px; flex: none; font-size: 0.85em; color: var(--primary-text-color); }
        .day.today { font-weight: 700; color: var(--accent-color, orange); }
        .track { position: relative; flex: 1; height: 22px; margin-top: 12px; }
        .track-bg { position: absolute; inset: 0; border-radius: 6px;
                    background: ${reduitColor}; opacity: 0.35; }
        .track.editable { cursor: crosshair; }
        .slot, .blk { position: absolute; top: 0; height: 100%; border-radius: 4px; }
        .slot.reduit { background: transparent; z-index: 1; }
        .blk.reduit { z-index: 1; }
        .chg { position: absolute; top: -12px; width: 0; z-index: 2; }
        .chg::before { content: ""; position: absolute; left: -1px; top: 2px;
                      width: 2px; height: 20px;
                      background: var(--primary-text-color, #333); opacity: 0.55; border-radius: 1px; }
        .chg span { position: absolute; top: -11px; left: 0; transform: translateX(-50%);
                   white-space: nowrap; font-size: 0.62em; color: var(--secondary-text-color); }
        .tooltip { position: fixed; z-index: 999; pointer-events: none;
                   background: var(--card-background-color, #fff);
                   color: var(--primary-text-color, #111);
                   border: 1px solid var(--divider-color, #ccc);
                   border-radius: 6px; padding: 4px 8px; font-size: 0.8em;
                   box-shadow: 0 2px 8px rgba(0,0,0,0.25); display: none; }
        .scale { position: relative; height: 18px; margin-left: 82px; }
        .tick { position: absolute; transform: translateX(-50%);
                font-size: 0.7em; color: var(--secondary-text-color); }
        .legend { display: flex; gap: 16px; margin-top: 10px; font-size: 0.85em;
                 color: var(--primary-text-color); }
        .edit-ranges { display: flex; flex-wrap: wrap; gap: 4px 12px;
                       margin: -2px 0 8px 82px; font-size: 0.72em;
                       color: var(--secondary-text-color); }
        .range { white-space: nowrap; }
        .range::before { content: ""; display: inline-block; width: 7px; height: 7px;
                         margin-right: 4px; border-radius: 50%; vertical-align: 1px; }
        .range.confort::before { background: ${confortColor}; }
        .range.reduit::before { background: ${reduitColor}; }
        .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%;
              margin-right: 5px; vertical-align: middle; }
        .actions { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
        .btn { border: 1px solid var(--divider-color, #ccc); border-radius: 18px;
              background: var(--card-background-color, #fff); color: var(--primary-text-color);
              padding: 6px 18px; font-size: 0.9em; cursor: pointer; }
        .btn:hover:not(:disabled) { filter: brightness(0.9); }
        .btn:disabled { opacity: 0.5; cursor: default; }
        .hint { font-size: 0.75em; color: var(--secondary-text-color); }
        .status { font-size: 0.85em; }
        .status.ok { color: var(--primary-text-color); }
        .status.err { color: var(--error-color, red); }
      </style>
      <ha-card>
        ${this.config.title ? `<div class="title">${this.config.title}</div>` : ""}
        <div class="rows">${rows}</div>
        <div class="scale">${scale}</div>
        <div class="legend">
          <span><span class="dot" style="background:${confortColor}"></span>Confort</span>
          <span><span class="dot" style="background:${reduitColor}"></span>Réduit</span>
        </div>
        ${actions}
        <div class="tooltip"></div>
      </ha-card>`;

    this._wireEvents();
  }

  // ---------------------------------------------------------------- events

  _wireEvents() {
    const root = this._renderRoot;

    // Infobulles (lecture seule)
    const tip = root.querySelector(".tooltip");
    root.querySelectorAll(".blk").forEach((el) => {
      el.addEventListener("mouseenter", () => {
        tip.textContent = el.dataset.tip;
        tip.style.display = "block";
      });
      el.addEventListener("mousemove", (e) => {
        tip.style.left = `${e.clientX + 12}px`;
        tip.style.top = `${e.clientY + 12}px`;
      });
      el.addEventListener("mouseleave", () => { tip.style.display = "none"; });
    });

    // Boutons
    const btnEdit = root.querySelector("#btn-edit");
    if (btnEdit) btnEdit.addEventListener("click", () => {
      const prog = (this._getEntity() || { attributes: {} }).attributes.programmation;
      this._initEditBuffer(this._optimistic || prog);
      this._editMode = true;
      this._status = null;
      this._render();
    });

    const btnCancel = root.querySelector("#btn-cancel");
    if (btnCancel) btnCancel.addEventListener("click", () => {
      this._editMode = false;
      this._saving = false;
      this._status = null;
      this._render();
    });

    const btnSave = root.querySelector("#btn-save");
    if (btnSave) btnSave.addEventListener("click", () => this._save());

    // Édition : clic + glissement sur les pistes
    if (this._editMode) {
      root.querySelectorAll(".track.editable").forEach((track) => {
        track.addEventListener("pointerdown", (e) => {
          e.preventDefault();
          this._painting = true;
          this._paintValue = null;
          try { track.setPointerCapture(e.pointerId); } catch (_) {}
          this._paintSlot(track, e);
        });
        track.addEventListener("pointermove", (e) => {
          if (this._painting) this._paintSlot(track, e);
        });
        track.addEventListener("pointerup", () => {
          if (this._painting) { this._painting = false; this._render(); }
        });
        track.addEventListener("pointercancel", () => { this._painting = false; });
      });
    }
  }

  _paintSlot(track, e) {
    const day = Number(track.dataset.day);
    const rect = track.getBoundingClientRect();
    const ratio = Math.min(0.9999, Math.max(0, (e.clientX - rect.left) / rect.width));
    const idx = Math.floor(ratio * 48);
    if (idx < 0 || idx > 47) return;
    if (this._paintValue === null)
      this._paintValue = this._edit.data[day][idx] === 1 ? 0 : 1;
    if (this._edit.data[day][idx] !== this._paintValue) {
      this._edit.data[day][idx] = this._paintValue;
      this._edit.dirty = true;
    }
    this._updateTrackVisual(track);
  }

  // Rafraîchit la piste éditée sans tout réafficher (fluide pendant le glissement).
  _updateTrackVisual(track) {
    const day = Number(track.dataset.day);
    const confortColor = this.config.confort_color || "#ff5252";
    const plages = this._edit.data[day];
    let html = '<div class="track-bg"></div>';
    let i = 0;
    while (i < plages.length) {
      const v = plages[i];
      let j = i;
      while (j < plages.length && plages[j] === v) j++;
      const left = (i / 48) * 100;
      const width = ((j - i) / 48) * 100;
      html += `<div class="slot ${v === 1 ? "confort" : "reduit"}" data-day="${day}" data-idx="${i}"
            style="left:${left}%;width:${width}%;${v === 1 ? `background:${confortColor}` : ""}"></div>`;
      i = j;
    }
    track.innerHTML = html;
  }

  // ----------------------------------------------------------------  envoi

  async _save() {
    if (!this._hass || !this._edit || this._saving) return;
    this._saving = true;
    this._status = { ok: true, text: "Envoi en cours…" };
    this._render();

    // Payload Frisquet : 7 jours {jour, plages[48]} — jour 0 = dimanche.
    const programmation = [];
    for (let d = 0; d < 7; d++)
      programmation.push({ jour: d, plages: this._edit.data[d].slice() });

    const svc = this.config.service || "frisquet_connect.set_programmation";
    const parts = svc.split(".");
    const domain = parts.length === 2 ? parts[0] : "frisquet_connect";
    const name = parts.length === 2 ? parts[1] : "set_programmation";

    try {
      await this._hass.callService(domain, name, {
        entity_id: this.config.entity,
        programmation: programmation,
      });
      this._status = { ok: true, text: "Programmation envoyée à la chaudière" };
      this._optimistic = programmation;
      this._editMode = false;
      this._edit = null;
    } catch (err) {
      this._status = { ok: false, text: `Échec : ${err.message || err}` };
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
  description: "Frise hebdomadaire interactive de la programmation Frisquet (Confort / Réduit)",
});
