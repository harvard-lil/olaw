/**
 * @typedef {object} OpenLegalRagState - App-wide "state". All components are assumed to be able to read and write from this object.
 * @property {boolean} processing - If `true`, the app is considered "busy". Used to control UI state.
 * @property {{role: string, content: string}[]} history - Keeps track of "basic" chat history. To be fed back to the API with each exchange.
 * @property {string[]} availableModels - List of models that can be used.
 * @property {string} defaultModel - Model to be used by default.
 * @property {?string} searchStatement - Latest `search_target` returned by the API (`/api/extract-search-statement`).
 * @property {?string} searchTarget - Latest `search_target` returned by the API (`/api/extract-search-statement`).
 * @property {object} searchResults - Latest output from `/api/search`.
 * @property {?string} message - Latest message typed by the user.
 * @property {?string} model - Latest model picked by the user.
 * @property {?Number} maxTokens - Latest value picked by the user for "max tokens".
 */

/**
 * Basic app-wide "state"
 * @type {OpenLegalRagState}
 */
export const state = {
  processing: false,
  history: [],
  availableModels: window.OPEN_LEGAL_RAG_CONST.available_models,
  defaultModel: window.OPEN_LEGAL_RAG_CONST.default_model,
  searchStatement: null,
  searchTarget: null,
  searchResults: null,
  message: null,
  model: window.OPEN_LEGAL_RAG_CONST.default_model,
  temperature: 0.0,
  maxTokens: null,
};
