const CARD_VERSION = "0.1.0";

class HuaweiSmsCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Vous devez définir entity");
    this._config = { title: "Messages du modem", show_unread_only: false, ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return Math.max(3, Math.min(8, this._messages().length + 2));
  }

  _messages() {
    const messages = this._hass?.states?.[this._config?.entity]?.attributes?.messages;
    if (!Array.isArray(messages)) return [];
    return this._config.show_unread_only
      ? messages.filter((message) => message.unread)
      : messages;
  }

  _element(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  _button(label, title, action, className = "") {
    const button = this._element("button", className, label);
    button.type = "button";
    button.title = title;
    button.addEventListener("click", action);
    return button;
  }

  _formatDate(value) {
    if (!value) return "";
    const parsed = new Date(String(value).replace(" ", "T"));
    return Number.isNaN(parsed.getTime())
      ? String(value)
      : new Intl.DateTimeFormat(this._hass?.locale?.language || undefined, {
          dateStyle: "short",
          timeStyle: "short",
        }).format(parsed);
  }

  async _callService(service, data) {
    try {
      await this._hass.callService("huawei_sms", service, data);
    } catch (error) {
      const event = new Event("hass-notification", { bubbles: true, composed: true });
      event.detail = { message: `Huawei SMS: ${error.message || error}` };
      this.dispatchEvent(event);
    }
  }

  _compose(phoneNumber = "") {
    const recipient = phoneNumber || window.prompt("Numéro du destinataire", "+33");
    if (!recipient?.trim()) return;
    const message = window.prompt(`SMS vers ${recipient}`);
    if (message === null || !message.trim()) return;
    this._callService("send", {
      phone_number: recipient.trim(),
      message: message.trim(),
    });
  }

  _delete(message) {
    const sender = message.contact_name || message.from || "cet expéditeur";
    if (!window.confirm(`Supprimer définitivement le SMS de ${sender} ?`)) return;
    this._callService("delete", { message_id: Number(message.id) });
  }

  _renderMessage(message) {
    const item = this._element("article", `message${message.unread ? " unread" : ""}`);
    const header = this._element("div", "message-header");
    const identity = this._element("div", "identity");
    identity.append(
      this._element(
        "strong",
        "sender",
        message.contact_name || message.from || "Numéro inconnu",
      ),
      this._element(
        "span",
        "number",
        message.contact_name && message.from ? message.from : "",
      ),
    );
    header.append(identity, this._element("time", "date", this._formatDate(message.date)));

    const actions = this._element("div", "actions");
    if (message.from) {
      actions.append(
        this._button("Répondre", "Répondre à ce SMS", () => this._compose(message.from)),
      );
    }
    if (message.id !== undefined && message.id !== "") {
      actions.append(
        this._button(
          "Supprimer",
          "Supprimer ce SMS",
          () => this._delete(message),
          "danger",
        ),
      );
    }
    item.append(header, this._element("p", "content", message.content || ""), actions);
    return item;
  }

  _render() {
    if (!this.shadowRoot || !this._config) return;
    this.shadowRoot.replaceChildren();

    const style = document.createElement("style");
    style.textContent = `
      :host { display: block; }
      ha-card { overflow: hidden; }
      .toolbar { align-items: center; display: flex; gap: 12px; padding: 16px; }
      h2 { flex: 1; font-size: 1.15rem; margin: 0; }
      .count { color: var(--secondary-text-color); font-size: .9rem; }
      .list { border-top: 1px solid var(--divider-color); }
      .message { padding: 14px 16px; }
      .message + .message { border-top: 1px solid var(--divider-color); }
      .message.unread { border-left: 4px solid var(--primary-color); padding-left: 12px; }
      .message-header { align-items: start; display: flex; gap: 12px; }
      .identity { display: flex; flex: 1; flex-direction: column; min-width: 0; }
      .sender, .number, .date { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .number, .date { color: var(--secondary-text-color); font-size: .8rem; }
      .content { overflow-wrap: anywhere; white-space: pre-wrap; }
      .actions { display: flex; gap: 8px; justify-content: flex-end; }
      button { background: transparent; border: 0; color: var(--primary-color); cursor: pointer; font: inherit; padding: 8px; }
      button.danger { color: var(--error-color); }
      .empty, .error { color: var(--secondary-text-color); padding: 24px 16px; text-align: center; }
      .error { color: var(--error-color); }
    `;

    const card = document.createElement("ha-card");
    const entity = this._hass?.states?.[this._config.entity];
    const messages = this._messages();
    const toolbar = this._element("div", "toolbar");
    toolbar.append(
      this._element("h2", "", this._config.title),
      this._element("span", "count", `${messages.length} SMS`),
      this._button("Nouveau", "Écrire un SMS", () => this._compose()),
    );
    card.append(toolbar);

    if (this._hass && !entity) {
      card.append(
        this._element("div", "error", `Entité introuvable : ${this._config.entity}`),
      );
    } else if (entity && messages.length === 0) {
      card.append(this._element("div", "empty", "Aucun SMS à afficher"));
    } else if (messages.length) {
      const list = this._element("div", "list");
      list.append(...messages.map((message) => this._renderMessage(message)));
      card.append(list);
    }
    this.shadowRoot.append(style, card);
  }
}

if (!customElements.get("huawei-sms-card")) {
  customElements.define("huawei-sms-card", HuaweiSmsCard);
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "huawei-sms-card",
  name: "Huawei HiLink SMS",
  description: "Affiche et gère les SMS d’un modem Huawei HiLink.",
  preview: false,
  version: CARD_VERSION,
});
