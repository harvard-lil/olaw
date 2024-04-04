import { state } from "../state.js";

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
          state.log(
            "User accepted suggested search.",
            "/api/extract-search-statement"
          );

          confirmButton.setAttribute("disabled", "disabled");
          rejectButton.setAttribute("disabled", "disabled");

          document.querySelector("chat-flow").search();
        });

        // Event listener for the "reject" button:
        rejectButton.addEventListener("click", (e) => {
          state.log(
            "User rejected suggested search.",
            "/api/extract-search-statement"
          );

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
    <p class="actor">${this.sanitizeString(state.model)}</p>
    <p class="text"></p>
    `;
  };

  /**
   * Renders an "analyzing-request" bubble.
   * @returns {void}
   */
  renderAnalyzingRequestBubble = () => {
    this.innerHTML = /*html*/ `
    <p class="actor">System</p>
    <p class="text">The chatbot is looking for a tool to help answer your question.</p>
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
    <p class="actor">${this.sanitizeString(state.model)}</p>
    <p class="text">
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
   * Renders an "sources" bubble listing everything under state.searchResults.
   * @returns {void}
   */
  renderSourcesBubble = () => {
    let sourcesText = "";

    for (const searchTarget of state.availableSearchTargets) {
      if (!state.searchResults[searchTarget]) {
        continue;
      }

      for (const source of state.searchResults[searchTarget]) {
        const text = this.sanitizeString(`${source.ui_text}`, false);
        const url = this.sanitizeString(source.ui_url, false);

        sourcesText += /*html*/ `
        <p class="text">
          <a href="${url}" target="_blank" title="Open source in new tab">
            ${text}
          </a>
        </p>
        `;
      }

      this.innerHTML = /*html*/ `
      <p class="actor">Source: <span>${searchTarget}</span></p>
      ${sourcesText ? sourcesText : "No results"}
      `;
    }
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
