import { state } from "/static/state.js";

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
  }

  /**
   * Adds text completion prompt transcript to logs
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
   * Adds search statement extraction prompt transcript to logs
   * @returns {void}
   */
  logExtractSearchStatementPrompt = () => {
    let prompt = state.extractSearchStatementPrompt.trim();
    this.log(prompt, "Transcript of the search statement extraction prompt");
  };

  /**
   * Add text to log
   * @returns {void}
   */
  log = (text, title = "") => {
    let output = "";

    output += "----------------------------------------\n";
    output += title ? `${title}\n` : ``;
    output += `${new Date()}\n`;
    output += "----------------------------------------\n";
    output += `${text}\n\n`;

    this.querySelector("textarea").textContent += output;
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

      <textarea disabled></textarea>
    </dialog>
    `;
  };
}
customElements.define("inspect-dialog", InspectDialog);
