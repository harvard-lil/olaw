import { state } from "/static/state.js";

export class InspectDialog extends HTMLElement {
  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();
  }

  /**
   * Opens underlying `<dialog>`
   * @returns {void}
   */
  open = () => {
    this.querySelector("dialog").showModal();
  };

  /**
   * Closes underlying `<dialog>`
   * @returns {void}
   */
  close = () => {
    this.querySelector("dialog").close();
  };

  renderInnerHTML = () => {
    this.innerHTML = /*html*/ `
    <dialog>
      <button class="close">Close</button>
      <h2>Inspect Session</h2>
    </dialog>
    `;
  };
}
customElements.define("inspect-dialog", InspectDialog);
