// TODO: Reorganize this file once logic is complete.

/*------------------------------------------------------------------------------
 * Module-level references / state
 -----------------------------------------------------------------------------*/

/** Keeps track of "basic" chat history. To be fed back to the API after each exchange. */
let history = [];

/** If `true`, user should not be able to send another request. */
let isLoading = false;

/** If `true`, indicates that the chatbot is awaiting non-text interaction (i.e: click on a button) */
let isAwaitingInteraction = false;

/** Latest "search_statement" returned by the API */
let searchStatement = null;

/** Latest "search_target" returned by the API */
let searchTarget = null;

/** Latest output from /api/legal/search */
let searchResults = {};

const modelSelect = document.querySelector("#model");
const temperatureSelect = document.querySelector("#temperature");
const maxTokensInput = document.querySelector("#max_tokens");

const chatConversation = document.querySelector("#chat-conversation");
const chatInput = document.querySelector("#chat-input");
const chatPlaceholder = document.querySelector("#chat .placeholder")

const messageInput = document.querySelector("#message");
const askButton = document.querySelector("button.ask");

/*------------------------------------------------------------------------------
 * Utility 
 -----------------------------------------------------------------------------*/
/**
 * Escapes a string so it can be rendered as part of an HTML document.
 * @param {string} string 
 * @param {boolean} convertLineBreaks - If true, replaces \n with <br>
 * @returns {string}
 */
const sanitizeString = (string, convertLineBreaks = true) => {
  string = string.trim()
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");

  if (convertLineBreaks === true) {
    string = string.replaceAll("\n", "<br>");
  }

  return string;
}

/**
 * Injects a specialized chat bubble into `#chat-conversation`.
 * Populates history on the fly.
 * @param {String} type - Can be "user", "ai", "error", "confirm-search", "source-courtlistener".
 * @param {String} content - Textual content to be added to the bubble. Can be empty if type is: "confirm-search", "ai" or "source-courtlistener".
 * @param {Object} metadata - Meta-data associated with that chat bubble. Expected for "source-courtlistener" (`searchResults.courtlistener` entry).
 * 
 * Uses module-level variables:
 * - searchStatement
 * - searchTarget
 * - searchResults
 */
const renderChatBubble = (type, message, metadata) => {
  switch(type) {
    //
    // "user"
    //
    case "user":
      chatConversation.insertAdjacentHTML(
        "beforeend", 
        /*html*/`
        <article class="message user" contenteditable>
          <p class="text">${sanitizeString(message)}</p>
        </article>`
      );

      history.push({"role": "user", "content": message});
      scrollIntoConversation();
    break;

    //
    // "ai"
    //
    case "ai":
      chatConversation.insertAdjacentHTML(
        "beforeend", 
        /*html*/`
        <article class="message ai">
          <p class="model">${sanitizeString(modelSelect.value)}</p>
          <p class="text" contenteditable></p>
        </article>`
      );

      raiseLoadingMode();
      // NOTE: History to be added once stream is complete -- see streamCompletion
      // NOTE: Stream scrolls into conversation automatically
    break;

    //
    // "confirm-search": Asks user to confirm search
    //
    case "confirm-search":
      const searchTargetName = searchTarget === "courtlistener" ? "the Court Listener API" : "";

      chatConversation.insertAdjacentHTML(
        "beforeend", 
        /*html*/`
        <article class="message confirm-search">
          <p class="text">
            The chatbot detected a legal question. 
            Run the following query against ${searchTargetName}?<br>
            <code>${sanitizeString(searchStatement)}</code>
          </p>

          <div class="actions">
            <button class="confirm-search-yes">Yes, perform search.</button>
            <button class="confirm-search-no">No.</button>
          </div>
        </article>`
      );

      raiseAwaitingInteractionMode();
      scrollIntoConversation();
    break;

    //
    // "source-courtlistener"
    //
    case "source-courtlistener":
      const url = sanitizeString(metadata.absolute_url, false);
      const year = sanitizeString(metadata.date_filed.substr(0,4), false);
      const name = sanitizeString(metadata.case_name, false);
      const court = sanitizeString(metadata.court, false);

      chatConversation.insertAdjacentHTML(
        "beforeend", 
        /*html*/`
        <article class="message source">
          <p class="text">
            <a href="${url}">${name} (${year})</a>
            <span>${court}</span>
            <em>Source: CourtListener.com</em>
          </p>
        </article>`
      );

      scrollIntoConversation();
    break;
  }
}

/**
 * Runs a request against /api/complete and stream results in a "AI" chat bubble.
 * 
 * Uses module-level variables:
 * - searchResults
 * - history
 * 
 * @returns {void}
 */
const streamCompletion = async () => {
  const message = history[history.length - 1]["content"];
  const model = modelSelect.value.trim();
  const temperature = temperatureSelect.value;
  const maxTokens = maxTokensInput.value === "" ? null : parseInt(maxTokensInput.value);

  let output = "";

  // Run completion request
  const response = await fetch("/api/complete", {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify({
      message, 
      model,
      temperature,
      max_tokens: maxTokens, 
      history,
      search_results: searchResults
    })
  });

  if (response.status != 200) {
    renderChatBubble("error", `Could not communicate with ${sanitizeString(model)}.`)
    return
  }

  // Append "ai" bubble
  renderChatBubble("ai", "");
  const aiBubbleText = chatConversation.querySelector("article:last-of-type .text");

  // Stream text into "ai" bubble as it comes
  const responseStream = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const {done, value} = await responseStream.read();

    const textChunk = decoder.decode(value, {stream:true});

    output += textChunk;
    aiBubbleText.innerText = aiBubbleText.innerText + textChunk;

    scrollIntoConversation();

    if (done) {
      break;
    }
  }

  // Add resulting message to history
  history.push({"role": "assistant", "content": output});

}

const raiseLoadingMode = () => {
  isLoading = true;
  messageInput.setAttribute("disabled", "disabled");
  messageInput.value = "Please wait ...";
}

const clearLoadingMode = () => {
  isLoading = false;
  messageInput.removeAttribute("disabled");
  messageInput.value = "";
}

const raiseAwaitingInteractionMode = () => {
  isAwaitingInteraction = true;
} 

const clearAwaitingInteractionMode = () => {
  isAwaitingInteraction = false;

  // Disable any remaining active interaction buttons in "#chat-conversation"
  for (const button of chatConversation.querySelectorAll("button")) {
    button.setAttribute("disabled", "disabled");
  }
} 

/**
 * Automatically scrolls down #chat-conversation
 */
const scrollIntoConversation = () => {
  chatConversation.scroll({
    top: chatConversation.scrollHeight,
    left: 0,
    behavior: "smooth"
  });
}

/*------------------------------------------------------------------------------
 * Chat Mechanism
 -----------------------------------------------------------------------------*/
/**
 * On "chat" form submit:
 * - Hide placeholder visual
 * - Inject user message into UI
 * - Trigger loading state 
 * - Run request against /api/legal/extract-search-statement
 * - If API returns a search_statement 
 *   - Ask user to confirm search
 *   - Confirms: 
 *     - Run query against /api/legal/search
 *     - Display results
 *     - Run and stream LLM completion with additional context
 * - If API returns no search_statement or user rejects suggestion:
 *   - Run and stream completion "as is"
 */
chatInput.addEventListener("submit", async (e) => {
  e.preventDefault();

  const message = messageInput.value.trim();
  const model = modelSelect.value.trim();
  const temperature = temperatureSelect.value;

  // Cannot submit if awaiting interaction
  if (isAwaitingInteraction) {
    return;
  }

  // Reset search state
  searchResults = {};
  searchStatement = "";
  searchTarget = "";

  // Trigger loading mode
  raiseLoadingMode();

  // Hide placeholder
  chatPlaceholder.classList.add("hidden");

  // Disable any remaining chat-level interaction buttons
  for (const button of chatConversation.querySelectorAll("button")) {
    button.setAttribute("disabled", "disabled");
  }

  // Inject user message in UI
  renderChatBubble("user", message)

  try {
    // Detect legal question / extract search statement
    const searchStatementResponse = await fetch("/api/legal/extract-search-statement", {
      method: "POST",
      headers: {"content-type": "application/json"},
      body: JSON.stringify({message, model, temperature})
    });

    const searchStatementData = await searchStatementResponse.json();

    // Search statement returned: Ask user to confirm search 
    if (searchStatementData && 
        searchStatementData?.search_statement && 
        searchStatementData?.search_target) {

        searchStatement = searchStatementData.search_statement;
        searchTarget = searchStatementData.search_target;
        renderChatBubble("confirm-search", "");
    }
    // Otherwise: stream completion
    else {
      await streamCompletion();
    }

    messageInput.value = "";
  } 
  // Catch-all: 
  // - Reset loading state
  // - Put user message back in input.
  catch(err) {
    clearAwaitingInteractionMode();
    clearLoadingMode();
    console.log(err);
  // In any case: clear loading mode.
  } finally {
    clearLoadingMode();
  }

});

/**
 * Handle clicks on "confirm-search" actions.
 * - YES: Perform search, display results, stream completion
 * - NO: Stream LLM completion
 */
chatConversation.addEventListener("click", async e => {
  // Stop here if chatbot is not awaiting interaction
  if (!isAwaitingInteraction ) {
    return;
  }

  // Stop here if target is not a "confirm-search" button
  if (!e.target.classList.contains("confirm-search-yes") && 
      !e.target.classList.contains("confirm-search-no")
  ) {
    return;
  }

  e.preventDefault();
  clearAwaitingInteractionMode();
  raiseLoadingMode();

  try {
    // User accepts suggested search query:
    // - Run search
    // - Display search results
    // - Run completion
    if (e.target.classList.contains("confirm-search-yes")) {
      const response =  await fetch("/api/legal/search", {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({
          search_statement: searchStatement, 
          search_target: searchTarget
        })
      });
  
      searchResults = await response.json();

      // Court Listener
      for (const entry of searchResults?.courtlistener) {
        renderChatBubble("source-courtlistener", "", entry);
        await new Promise(resolve => setTimeout(resolve), 250);
      }
    }
  } 
  // Catch-all: inject error message
  catch (err) {
    renderChatBubble("Could not perform requested search.");
  }
  // In any case:
  // - Disable buttons for that "confirm-search" action
  // - Stream completion
  // - Disable pending flag
  finally {
    await streamCompletion();
    clearLoadingMode();
  }

});

/**
 * Automatically activate / deactivate "Ask" button.
 * Runs every 100ms.
 */
setInterval(() => {
  const messageOk = messageInput.value.trim().length > 0;
  const modelOk = modelSelect.value.trim().length > 0;
  const temperatureOk = temperatureSelect.value.match(/[0-9]\.[0-9]/) != null;
  const maxTokensOk = maxTokensInput.value === "" || maxTokensInput.value.match(/[0-9]+/) != null;

  // Activate "Ask" button if all is OK
  if (!isLoading && 
      !isAwaitingInteraction && 
      messageOk && 
      modelOk && 
      temperatureOk && 
      maxTokensOk
  ) {
    askButton.removeAttribute("disabled");
  } else {
    askButton.setAttribute("disabled", "disabled");
  }
}, 100);

/*------------------------------------------------------------------------------
 * Handling of dialogs (generic)
 -----------------------------------------------------------------------------*/
document.querySelector("body").addEventListener("click", e => {
  // Open:
  // - Event target: buttons with "data-dialog-open" data attribute
  // - Opens: corresponding dialog[data-dialog]
  if (e.target?.dataset?.dialogOpen && e.target instanceof HTMLButtonElement) {
    e.preventDefault();
    const dialog = e.target.dataset.dialogOpen;
    document.querySelector(`dialog[data-dialog="${dialog}"]`).showModal();
  }

  // Close
  // - Event target: buttons with "close" class and `<dialog>` as a parent.
  // - Closes parent dialog.
  if (e.target.classList.contains("close") && e.target.parentNode instanceof HTMLDialogElement) {
    e.target.parentNode.close();
  }
});
