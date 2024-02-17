import { state } from "/static/state.js";

export class ChatInput extends HTMLElement {
  /** Holds interval function calling stateCheck */
  stateCheckInterval = null;

  /** Reference to form > textarea */
  inputTextAreaRef = null;

  /** Reference to form > .actions > button[data-action="stop-completion"] */
  stopCompletionButtonRef = null;

  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();

    // Grab shared element references
    this.inputTextAreaRef = this.querySelector("textarea");

    this.stopCompletionButtonRef = this.querySelector(
      `button[data-action="stop-completion"]`
    );

    // Event listeners for open-xyz (dialog triggers)
    for (const dialogName of ["settings", "inspect"]) {
      const button = this.querySelector(
        `button[data-action="open-${dialogName}"]`
      );

      button.addEventListener("click", (e) => {
        e.preventDefault();
        document.querySelector(`${dialogName}-dialog`).open();
      });
    }

    // Event listener for stop-completion (stops processing)
    this.stopCompletionButtonRef.addEventListener("click", (e) => {
      state.processing = false;
    });

    // Check every 100ms what parts of this component need to be disabled
    this.stateCheckInterval = setInterval(this.stateCheck, 100);
  }

  disconnectedCallback() {
    clearInterval(this.stateCheckInterval);
  }

  /**
   * Determines what parts of this component need to be disabled based on app state.
   */
  stateCheck = () => {
    // Textarea: disabled while processing
    if (state.processing) {
      this.inputTextAreaRef.setAttribute("disabled", "disabled");
      this.inputTextAreaRef.value = "Please wait ...";
    } else {
      this.inputTextAreaRef.removeAttribute("disabled");
      this.inputTextAreaRef.value = "";
    }

    // "Stop" button: enabled while processing
    if (state.processing) {
      this.stopCompletionButtonRef.removeAttribute("disabled");
    } else {
      this.stopCompletionButtonRef.setAttribute("disabled", "disabled");
    }
  };

  renderInnerHTML = () => {
    this.innerHTML = /*html*/ `
    <form>
      <textarea 
        id="message" 
        placeholder="This chatbot can use tools such at the Court Listener API to try to answer legal questions." 
        required></textarea>
      
      <div class="actions">
        <button class="hollow" data-action="open-settings">Settings</button>
        <button class="hollow" data-action="open-inspect">Inspect</button>
        <button class="hollow" data-action="stop-completion" disabled>Stop</button>
        <button class="ask" disabled>Ask</button>
      </div>
    </form>
    `;
  };
}
customElements.define("chat-input", ChatInput);
