import { state } from "/static/state.js";

/**
 * UI Element representing a chat bubble.
 *
 * Available values for "type" attribute:
 * - "user": User message
 * - "ai": Message from AI.
 * - "error": Standard error message.
 * - "analyzing-request": System message letting the user know that the system is analyzing the request.
 * - "confirm-search": Interactive message asking the user to confirm before performing a RAG search.
 * - "sources": Message listing sources (state.searchResults)
 *
 * Uses app state + type to determine what contents to render.
 */
export class ChatBubble extends HTMLElement {
  connectedCallback() {
    const type = this.getAttribute("type");

    switch (type) {
      case "user":
        this.renderUserBubble();
        break;

      case "ai":
        this.renderAIBubble();
        break;

      case "analyzing-request":
        this.renderAnalyzingRequestBubble();
        break;

      case "confirm-search":
        this.renderConfirmSearchBubble();

        const confirmButton = this.querySelector(`[data-action="confirm"]`);
        const rejectButton = this.querySelector(`[data-action="reject"]`);

        // Event listener for the "confirm" button
        confirmButton.addEventListener("click", (e) => {
          confirmButton.setAttribute("disabled", "disabled");
          rejectButton.setAttribute("disabled", "disabled");
          document.querySelector("chat-flow").search();
        });

        // Event listener for the "reject" button:
        rejectButton.addEventListener("reject", (e) => {
          confirmButton.setAttribute("disabled", "disabled");
          rejectButton.setAttribute("disabled", "disabled");
          document.querySelector("chat-flow").streamCompletion();
        });

        break;

      case "sources":
        this.renderSourcesBubble();
        break;

      case "error":
      default:
        this.renderErrorBubble();
        break;
    }
  }

  /**
   * Renders a "user" bubble.
   * Uses the current value of `state.message`.
   * @returns {void}
   */
  renderUserBubble = () => {
    this.innerHTML = /*html*/ `
    <p class="text">${this.sanitizeString(state.message)}</p>
    `;
  };

  /**
   * Renders an "ai" bubble.
   * Text starts empty and is later streamed from `<chat-flow>`.
   * @returns {void}
   */
  renderAIBubble = () => {
    this.innerHTML = /*html*/ `
    <p class="model">${this.sanitizeString(state.model)}</p>
    <p class="text"></p>
    `;
  };

  /**
   * Renders an "analyzing-request" bubble.
   * @returns {void}
   */
  renderAnalyzingRequestBubble = () => {
    this.innerHTML = /*html*/ `
    <p class="model">System</p>
    <p class="text">The chatbot is trying to identify a legal question in your request.</p>
    `;
  };

  /**
   * Renders an "confirm-search" bubble.
   * @returns {void}
   */
  renderConfirmSearchBubble = () => {
    const searchTargetName = this.sanitizeString(state.searchTarget);
    const searchStatement = this.sanitizeString(state.searchStatement);

    this.innerHTML = /*html*/ `
    <p class="model">${this.sanitizeString(state.model)}</p>
    <p class="text">
      The chatbot detected a legal question.<br/> 
      Run the following query against ${searchTargetName}?<br>
      <code>${searchStatement}</code>
    </p>

    <div class="actions">
      <button data-action="confirm">Yes, perform search.</button>
      <button data-action="reject">Skip.</button>
    </div>
    `;
  };

  /**
   * Renders an "sources" bubble.
   * @returns {void}
   */
  renderSourcesBubble = () => {
    const searchTargetName = this.sanitizeString(state.searchTarget);
    let sourcesText = "";

    // courtlistener
    for (const source of state.searchResults?.courtlistener) {
      const refTag = this.sanitizeString(`${source.ref_tag}`, false);
      const url = this.sanitizeString(source.absolute_url, false);
      const year = this.sanitizeString(source.date_filed.substr(0, 4), false);
      const name = this.sanitizeString(source.case_name, false);
      const court = this.sanitizeString(source.court, false);

      sourcesText += /*html*/ `
      <p class="text">
        <a href="${url}" target="_blank" title="Open opinion in new tab">
          [${refTag}] ${name} (${year})
        </a>
        <span>${court}</span>
        <em>Source: CourtListener.com</em>
      </p>
      `;
    }

    this.innerHTML = /*html*/ `
    <p class="model">${searchTargetName}</p>
    ${sourcesText}
    `;
  };

  /**
   * Renders an "error" bubble.
   * @returns {void}
   */
  renderErrorBubble = () => {
    this.innerHTML = /*html*/ `
    <p class="text">An error occurred (see console for details), please try again.</p>
    `;
  };

  /**
   * Escapes <, > and converts line breaks into <br>.
   * @param {string} string
   * @param {boolean} convertLineBreaks
   * @returns {void}
   */
  sanitizeString = (string, convertLineBreaks = true) => {
    string = string.trim().replaceAll("<", "&lt;").replaceAll(">", "&gt;");

    if (convertLineBreaks === true) {
      string = string.replaceAll("\n", "<br>");
    }

    return string;
  };
}
customElements.define("chat-bubble", ChatBubble);
