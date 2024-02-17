import { state } from "/static/state.js";

export class SettingsDialog extends HTMLElement {
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
    let modelSelectOptions = /*html*/ ``;
    let temperatureSelectOptions = /*html*/ ``;

    for (const model of state.availableModels) {
      modelSelectOptions += /*html*/ `
      <option 
        value="${model}" 
        ${model == state.defaultModel ? "selected" : ""}>
        ${model}
      </option>
      `;
    }

    for (let i = 0; i < 21; i++) {
      const temperature = (i / 10).toFixed(1);
      temperatureSelectOptions += /*html*/ `<option value="${temperature}">${temperature}</option>`;
    }

    this.innerHTML = /*html*/ `
    <dialog>
      <button class="close">Close</button>
      <h2>Settings</h2>

      <form>
        <label for="model">Model</label>
        <select id="model" name="model">
          ${modelSelectOptions}
        </select>

        <label for="temperature">Temperature</label>
        <select id="temperature" name="temperature">
          ${temperatureSelectOptions}
        </select>

        <label for="max_tokens">Max tokens</label>
        <input type="number" name="max_tokens" id="max_tokens" value="" placeholder="Default">
      </form>
    </dialog>
    `;
  };
}
customElements.define("settings-dialog", SettingsDialog);
