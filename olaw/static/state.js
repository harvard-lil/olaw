const constants = window.OPEN_LEGAL_RAG_CONST;

/**
 * @typedef {object} OpenLegalRagState - App-wide "state". All components are assumed to be able to read and write from this object.
 * @property {boolean} processing - If `true`, the app is considered "busy". Used to control UI state.
 * @property {boolean} streaming - If `true`, the app is currently streaming content. Used to control UI state.
 * @property {?string} searchStatement - Latest `search_target` returned by the API (`/api/extract-search-statement`).
 * @property {?string} searchTarget - Latest `search_target` returned by the API (`/api/extract-search-statement`).
 * @property {object} searchResults - Latest output from `/api/search`.
 * @property {?string} message - Latest message typed by the user.
 * @property {?string} model - Latest model picked by the user.
 * @property {?Number} maxTokens - Latest value picked by the user for "max tokens".
 * @property {{role: string, content: string}[]} history - Keeps track of "basic" chat history. To be fed back to the API with each exchange.
 * @property {?function} log - Shortcut for InspectDialog.log(text, title).
 * @property {string} basePrompt - Transcript of the base prompt.
 * @property {string} historyPrompt - Transcript of the history part of the prompt.
 * @property {string} ragPrompt - Transcript of the RAG (context) part of the prompt.
 * @property {string} extractSearchStatementPrompt - Transcript of the prompt used to extract search statement.
 * @property {string[]} availableModels - List of models that can be used.
 * @property {string} defaultModel - Model to be used by default.
 * @property {string[]} availableSearchTargets - List of valid search targets.
 */

/**
 * Basic "state" object used across the app to share data.
 * @type {OpenLegalRagState}
 */
export const state = {
  processing: false,
  streaming: false,
  searchStatement: "",
  searchTarget: "",
  searchResults: {},
  message: null,
  model: constants.default_model,
  temperature: 0.0,
  maxTokens: null,
  history: [],

  log: () => {},

  basePrompt: constants.text_completion_base_prompt,
  historyPrompt: constants.text_completion_history_prompt,
  ragPrompt: constants.text_completion_rag_prompt,
  extractSearchStatementPrompt: constants.extract_search_statement_prompt,
  availableModels: constants.available_models,
  defaultModel: constants.default_model,
  availableSearchTargets: constants.available_search_targets,
};
