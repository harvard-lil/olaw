import { state } from "/static/state.js";

/**
 * UI Element representing a chat bubble.
 *
 * Available values for "type":
 * - "user": User message
 * - "ai": Message from AI.
 * - "error": Standard error message.
 * - "analyzing-request": System message letting the user know that the system is analyzing the request.
 * - "confirm-search": Interactive message asking the user to confirm before performing a RAG search.
 * - "sources": Message listing sources (state.searchResults)
 *
 * Uses state to determine content.
 */
export class ChatBubble extends HTMLElement {
  static get observedAttributes() {
    return ["type"];
  }

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

        // Event listener for the "confirm" button
        this.querySelector(`button[data-action="confirm"]`).addEventListener(
          "click",
          (e) => {}
        );

        // Event listener for the "reject" button
        this.querySelector(`button[data-action="confirm"]`).addEventListener(
          "reject",
          (e) => {}
        );

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
    const searchTargetName = sanitizeString(state.searchTargetName);
    const searchStatement = sanitizeString(state.searchStatement);

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
    const searchTargetName = sanitizeString(state.searchTargetName);
    let sourcesText = "";

    // courtlistener
    for (const source of state.searchResults?.courtlistener) {
      const refTag = sanitizeString(`${source.ref_tag}`, false);
      const url = sanitizeString(source.absolute_url, false);
      const year = sanitizeString(source.date_filed.substr(0, 4), false);
      const name = sanitizeString(source.case_name, false);
      const court = sanitizeString(source.court, false);

      sourcesText += /*html*/ `
        <p class="text">
          <a href="${url}" target="_blank" title="Open case in new tab">
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
  renderAnalyzingRequestBubble = () => {
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
