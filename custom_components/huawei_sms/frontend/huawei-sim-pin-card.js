class HuaweiSimPinCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Vous devez définir entity");
    this._config = { title: "Code PIN SIM", ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    // Update status only: HA events must not erase a PIN being entered.
    this._updateStatus();
    this._setBusy(Boolean(this._busy));
  }

  getCardSize() { return 6; }
  getGridOptions() { return { columns: 12, rows: "auto", min_columns: 6 }; }

  _element(tag, text) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    return element;
  }

  _setBusy(busy) {
    this._busy = busy;
    this.shadowRoot?.querySelectorAll("button, input").forEach((element) => {
      element.disabled = busy || !this._hass;
    });
  }

  _updateStatus(status) {
    if (!this._status) return;
    const data = status ?? this._hass?.states?.[this._config.entity]?.attributes?.pin_status ?? {};
    const labels = {
      sim_state: "État SIM (code modem)",
      pin_opt_state: "Protection PIN (code modem)",
      pin_attempts_remaining: "Tentatives PIN restantes",
      puk_attempts_remaining: "Tentatives PUK restantes",
    };
    this._status.replaceChildren();
    for (const [key, label] of Object.entries(labels)) {
      this._status.append(
        this._element("dt", label),
        this._element("dd", data[key] ?? "Non lu / indisponible"),
      );
    }
  }

  async _readStatus() {
    const result = await this._hass.callWS({
      type: "call_service", domain: "huawei_sms", service: "get_pin_status",
      service_data: {}, return_response: true,
    });
    this._updateStatus(result.response);
  }

  async _run(service) {
    if (this._busy || !this._hass) return;
    if (service !== "get_pin_status") {
      if (!this._current.reportValidity()) return;
      if (service === "change_pin") {
        if (!this._new.reportValidity() || !this._confirm.reportValidity()) return;
        if (this._new.value !== this._confirm.value) {
          this._notice.textContent = "Les nouveaux codes PIN ne correspondent pas.";
          return;
        }
      }
      const questions = {
        verify_pin: "Déverrouiller la SIM avec ce code PIN ?",
        enable_pin: "Activer la demande du code PIN sur cette SIM ?",
        disable_pin: "Désactiver la demande du code PIN sur cette SIM ?",
        change_pin: "Remplacer le code PIN de cette SIM ?",
      };
      if (!window.confirm(questions[service])) return;
    }
    this._setBusy(true);
    this._notice.textContent = "Opération en cours…";
    try {
      if (service === "get_pin_status") {
        await this._readStatus();
        this._notice.textContent = "Statut actualisé.";
      } else {
        const data = { current_pin: this._current.value };
        if (service === "change_pin") data.new_pin = this._new.value;
        // Clear fields immediately; never retain PINs in card configuration/storage.
        this._clearPins();
        await this._hass.callService("huawei_sms", service, data);
        this._updateStatus({});
        this._notice.textContent = "Modification effectuée.";
        try {
          await this._readStatus();
        } catch {
          this._notice.textContent = "Modification effectuée. Statut indisponible : utilisez « Lire le statut ».";
        }
      }
    } catch {
      this._notice.textContent = service === "get_pin_status"
        ? "Lecture impossible. Vérifiez que les actions PIN sont chargées et le modem accessible."
        : "Opération refusée ou résultat incertain. Lisez le statut et vérifiez le PIN avant un nouvel essai.";
    } finally {
      if (service !== "get_pin_status") this._clearPins();
      this._setBusy(false);
    }
  }

  _clearPins() {
    for (const input of [this._current, this._new, this._confirm]) input.value = "";
  }

  _pinField(labelText) {
    const label = this._element("label", labelText);
    const input = this._element("input");
    input.type = "password";
    input.inputMode = "numeric";
    input.autocomplete = "off";
    input.pattern = "[0-9]{4,8}";
    input.minLength = 4;
    input.maxLength = 8;
    input.required = true;
    input.placeholder = "4 à 8 chiffres";
    label.append(input);
    return { label, input };
  }

  _render() {
    this.shadowRoot.replaceChildren();
    const style = this._element("style");
    style.textContent = `
      :host { display: block; }
      ha-card { padding: 16px; }
      h2 { font-size: 1.15rem; margin: 0 0 16px; }
      dl { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
      dt, p { color: var(--secondary-text-color); }
      dd { margin: 0; overflow-wrap: anywhere; }
      label { display: block; margin: 12px 0; }
      input { box-sizing: border-box; display: block; width: 100%; padding: 10px;
        margin-top: 6px; font: inherit; color: var(--primary-text-color);
        background: var(--card-background-color); border: 1px solid var(--divider-color);
        border-radius: 6px; }
      .actions { display: flex; flex-wrap: wrap; gap: 8px; }
      button { padding: 10px; font: inherit; cursor: pointer; border-radius: 6px;
        border: 1px solid var(--divider-color); color: var(--primary-color);
        background: var(--card-background-color); }
      button:disabled { opacity: .5; cursor: default; }
      .notice { min-height: 1.4em; }
    `;
    const card = this._element("ha-card");
    this._status = this._element("dl");
    this._notice = this._element("p");
    this._notice.className = "notice";
    this._notice.setAttribute("role", "status");
    this._notice.setAttribute("aria-live", "polite");
    const current = this._pinField("PIN actuel");
    const next = this._pinField("Nouveau PIN (pour le changement)");
    const confirm = this._pinField("Confirmer le nouveau PIN");
    [this._current, this._new, this._confirm] = [current.input, next.input, confirm.input];
    const actions = this._element("div");
    actions.className = "actions";
    for (const [service, text] of Object.entries({
      get_pin_status: "Lire le statut", verify_pin: "Déverrouiller la SIM",
      enable_pin: "Activer le PIN",
      disable_pin: "Désactiver le PIN", change_pin: "Changer le PIN",
    })) {
      const button = this._element("button", text);
      button.type = "button";
      button.addEventListener("click", () => this._run(service));
      actions.append(button);
    }
    card.append(this._element("h2", this._config.title), this._status,
      this._element("p", "Le code PIN actuel ne peut pas être lu. Un PIN incorrect consomme une tentative et peut nécessiter le code PUK."),
      current.label, next.label, confirm.label, actions, this._notice);
    this.shadowRoot.append(style, card);
    this._updateStatus();
    this._setBusy(false);
  }
}

if (!customElements.get("huawei-sim-pin-card")) {
  customElements.define("huawei-sim-pin-card", HuaweiSimPinCard);
}
window.customCards = window.customCards || [];
window.customCards.push({
  type: "huawei-sim-pin-card", name: "Huawei HiLink — Code PIN SIM",
  description: "Statut SIM, activation, désactivation et changement du code PIN.",
  preview: false,
});
