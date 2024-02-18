import { state } from "../state.js";

/**
 * UI Element containing:
 * - Journal of interactions between user and API
 *
 * Hoists `log()` method to state via `state.log()`.
 */
export class InspectDialog extends HTMLElement {
  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();
    this.logTextCompletionPrompt();
    this.logExtractSearchStatementPrompt();

    // Event listener for "close"
    this.querySelector(".close").addEventListener("click", this.close);

    // Hoist log function to state.log
    state.log = this.log;
  }

  /**
   * Add given text to logs.
   * Automatically adds system info if state.processing is `true`.
   * @param {String} text - Text to be logged.
   * @param {?String} title - Title for log section.
   * @returns {void}
   */
  log = (text, title = "") => {
    let output = "";

    output += "----------------------------------------\n";
    output += title ? `${title}\n` : ``;
    output += `${new Date()}\n`;
    output += "----------------------------------------\n";

    if (state.processing) {
      output += `Model: ${state.model}\n`;
      output += `Temperature: ${state.temperature}\n`;
      output += `Search Statement: ${state.searchStatement}\n`;
      output += `Search Target: ${state.searchTarget}\n\n`;
    }

    output += `${text}\n\n`;

    this.querySelector("#logs").textContent += output;
    console.log(output);
  };

  /**
   * Adds text completion prompt transcript to logs.
   * @return {void}
   */
  logTextCompletionPrompt = () => {
    let prompt = state.basePrompt.trim();
    prompt = prompt.replace("{history}", state.historyPrompt.trim());
    prompt = prompt.replace("{rag}", state.ragPrompt.trim());
    prompt = prompt.trim();
    this.log(prompt, "Transcript of the text completion prompt");
  };

  /**
   * Adds search statement extraction prompt transcript to logs.
   * @returns {void}
   */
  logExtractSearchStatementPrompt = () => {
    let prompt = state.extractSearchStatementPrompt.trim();
    this.log(prompt, "Transcript of the search statement extraction prompt");
  };

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

      <p>This information is also available in the browser's JavaScript console.</p>

      <div id="logs"></div>
    </dialog>
    `;
  };
}
customElements.define("inspect-dialog", InspectDialog);
