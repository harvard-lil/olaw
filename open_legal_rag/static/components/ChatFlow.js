import { state } from "/static/state.js";

/**
 * UI Element containing:
 * - List of chat "bubbles" from the user, AI and system.
 *
 * Handles the processing of requests via its `ask()` method.
 *
 * Automatically populates:
 * - `state.history`
 * - `state.searchStatement`
 * - `state.searchTarget`
 * - `state.searchResults`
 *
 * Automatically enable / disable relevant inputs based on app state.
 */
export class ChatFlow extends HTMLElement {
  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();
  }

  /**
   * @returns {void}
   */
  ask = () => {};

  /**
   *
   * @param {string} type
   * @param {string} message
   * @param {object} metadata
   * @returns {void}
   */
  addBubble = (type, message, metadata) => {};

  /**
   *
   * @param {string} chunk
   * @returns {void}
   */
  streamTextIntoLastAIBubble = (chunk) => {};

  renderInnerHTML = () => {
    this.innerHTML = /*html*/ `
      <img class="placeholder" 
            src="/static/images/illustration.png"
            aria-hidden="true"
            alt="" />
    `;
  };
}
customElements.define("chat-flow", ChatFlow);
