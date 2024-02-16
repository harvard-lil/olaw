import { state } from "/static/state.js";

export class SettingsDialog extends HTMLElement {
  static get observedAttributes() {}

  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();
  }

  attributeChangedCallback(name, oldValue, newValue) {}

  renderInnerHTML() {}
}
customElements.define("settings-dialog", SettingsDialog);
