import { state } from "/static/state.js";

export class ChatBubble extends HTMLElement {
  static get observedAttributes() {}

  connectedCallback() {
    this.renderInnerHTML();
  }

  attributeChangedCallback(name, oldValue, newValue) {}

  renderInnerHTML() {}
}
customElements.define("chat-bubble", ChatBubble);
