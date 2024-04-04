import { state } from "../state.js";

/**
 * UI Element containing:
 * - List of chat "bubbles" from the user, AI and system.
 *
 * Handles the processing of requests via its `ask()` and `search()` methods.
 *
 * Automatically populates:
 * - `state.processing`
 * - `state.history`
 * - `state.searchStatement`
 * - `state.searchTarget`
 * - `state.searchResults`
 *
 * Automatically enables / disables relevant inputs based on app state.
 */
export class ChatFlow extends HTMLElement {
  /** Reference to the paragraph with the last "ai" bubble in which text should be streamed. */
  currentAICursorRef = null;

  connectedCallback() {
    // Enforce singleton
    for (const node of [...document.querySelectorAll("chat-flow")].slice(1)) {
      node.remove();
    }

    this.renderInnerHTML();
  }

  /**
   * Processes a request from user (main entry point)
   * @returns {Promise<void>}
   */
  ask = async () => {
    // Remove placeholder if still present
    this.querySelector(".placeholder")?.remove();

    // Compile payload
    const message = state.message;
    const model = state.model;
    const temperature = state.temperature;

    if (!message || !model || temperature === null) {
      this.addBubble("error");
      this.end();
      return;
    }

    // Block UI
    state.processing = true;

    // Inject user message
    this.addBubble("user");
    state.log(state.message, "User sent a message");

    // Inject "analyzing-request" message
    await new Promise((resolve) => setTimeout(resolve, 500));
    this.addBubble("analyzing-request");

    // Analyze user request to identify potential legal question
    try {
      const response = await fetch("/api/extract-search-statement", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message, model, temperature }),
      });

      const data = await response.json();

      if (data?.search_statement && data?.search_target) {
        state.searchStatement = data.search_statement;
        state.searchTarget = data.search_target;
      }
    } catch (err) {
      console.error(err);
      this.addBubble("error");
      this.end();
      return;
    }

    // If legal question was asked:
    // - Inject "confirm-search" bubble
    // - Interaction with "confirm-search" will determine next step (search() / streamCompletion())
    if (state.searchStatement && state.searchTarget) {
      state.log(
        "Found a legal question. Awaiting for user confirmation before performing search.",
        "/api/extract-search-statement"
      );

      this.addBubble("confirm-search");
    }
    // If no legal question was asked:
    // - Inject "ai" bubble
    // - Start streaming completion
    else {
      state.log(
        "Did not find legal question. Starting text completion.",
        "/api/extract-search-statement"
      );

      this.streamCompletion();
    }
  };

  /**
   * Stops streaming.
   * @returns {void}
   */
  stopStreaming = () => {
    state.log("Streaming interrupted by user.");
    state.streaming = false;
  };

  /**
   * Ends System/AI turn, goes back to user for input.
   * @returns {void}
   */
  end = () => {
    state.processing = false;
    document.querySelector("chat-input textarea").value = "";
  };

  /**
   * Inserts a chat bubble of a given type at the end of `chat-flow`.
   * @param {string} type
   * @returns {void}
   */
  addBubble = (type) => {
    const bubble = document.createElement("chat-bubble");
    bubble.setAttribute("type", type);

    this.insertAdjacentElement("beforeend", bubble);

    if (type === "ai") {
      this.currentAICursorRef = bubble.querySelector(".text");
    }

    this.scrollIntoConversation();
  };

  /**
   * Performs a search against /api/search using search statement and target returned by /api/extract-search-statement.
   * Populates state.searchResults if successful.
   * Adds sources bubbles when search is complete
   * @returns {Promise<void>}
   */
  search = async () => {
    // Compile payload
    const searchStatement = state.searchStatement;
    const searchTarget = state.searchTarget;

    if (!searchStatement || !searchTarget) {
      this.addBubble("error");
      return;
    }

    // Run query and:
    // - Store results
    // - Inject "sources" bubble if necessary
    // - In any case: start streaming response
    try {
      let totalResults = 0;

      const response = await fetch("/api/search", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          search_statement: searchStatement,
          search_target: searchTarget,
        }),
      });

      if (response.status !== 200) {
        throw new Error((await response.json())?.error);
      }

      state.searchResults = await response.json();
      state.log(JSON.stringify(state.searchResults, null, 2), "/api/search");

      for (const key of state.availableSearchTargets) {
        totalResults += state.searchResults[key]?.length;
      }

      if (totalResults >= 0) {
        this.addBubble("sources");
      }
    } catch (err) {
      this.addBubble("error");
      console.error(err);
    } finally {
      this.streamCompletion();
    }
  };

  /**
   * Sends completion request to API and streams results into the last <chat-bubble type="ai"> of the list.
   * Payload is determined by app state.
   * @returns {Promise<void>}
   */
  streamCompletion = async () => {
    let output = "";
    let response = null;
    let responseStream = null;
    const decoder = new TextDecoder();

    //
    // Compile payload
    //
    const message = state.message;
    const model = state.model;
    const temperature = state.temperature;
    const maxTokens = state.maxTokens;
    const searchResults = state.searchResults;
    const history = state.history;

    if (!message || !model || temperature === null) {
      this.addBubble("error");
      return;
    }

    //
    // Start completion request
    //
    try {
      response = await fetch("/api/complete", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          message,
          model,
          temperature,
          max_tokens: maxTokens,
          history,
          search_results: searchResults,
        }),
      });

      if (response.status != 200) {
        throw new Error((await response.json())?.error);
      }
    } catch (err) {
      this.addBubble("error");
      console.error(err);
      this.end();
      return;
    }

    //
    // Stream text into "ai" bubble as it comes
    //
    try {
      state.streaming = true;
      responseStream = response.body.getReader();

      // Inject "ai" bubble to stream into
      this.addBubble("ai");

      // Stream
      while (true) {
        const { done, value } = await responseStream.read();

        const textChunk = decoder.decode(value, { stream: true });
        this.pushAITextChunk(textChunk);
        output += textChunk;

        if (done || !state.streaming) {
          break;
        }
      }

      // Log and add interaction to history
      state.log(output, "/api/complete");
      state.history.push({ role: "user", content: state.message });
      state.history.push({ role: "assistant", content: output });
    } finally {
      // Clear state of that interaction
      state.searchStatement = "";
      state.searchTarget = "";
      state.searchResults = {};
      state.message = "";

      state.streaming = false;
      this.end();
    }
  };

  /**
   * Pushes a chunk of text into last <chat-bubble type="ai"> of the list.
   * @param {string} chunk
   * @returns {void}
   */
  pushAITextChunk = (chunk) => {
    // Strip common markdown markers
    // [!] Temporary - should be replaced by proper markdown strip or interpreter.
    chunk = chunk.replace("**", "");
    chunk = chunk.replace("##", "");
    chunk = chunk.replace("###", "");

    const cursor = this.currentAICursorRef;
    cursor.textContent = cursor.textContent + chunk;

    this.scrollIntoConversation();
  };

  /**
   * Automatically scroll to the bottom of the conversation.
   * Disabled if state.reducedMotion is `true`.
   */
  scrollIntoConversation = () => {
    if (state.reducedMotion === true) {
      return;
    }

    this.scroll({
      top: this.scrollHeight,
      left: 0,
      behavior: "smooth",
    });
  };

  renderInnerHTML = () => {
    this.innerHTML = /*html*/ `
      <img class="placeholder" 
            src="/static/images/logo.svg"
            aria-hidden="true"
            alt="" />
    `;
  };
}
customElements.define("chat-flow", ChatFlow);
