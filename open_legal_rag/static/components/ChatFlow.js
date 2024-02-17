import { state } from "/static/state.js";

export class ChatFlow extends HTMLElement {
  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();
  }

  renderInnerHTML = () => {
    //
    // Render visual if history is empty
    //
    if (state.history.length < 1) {
      this.innerHTML = /*html*/ `
      <img class="placeholder" 
           src="/static/images/illustration.png"
           aria-hidden="true"
           alt="" />
      `;
    }
  };
}
customElements.define("chat-flow", ChatFlow);
