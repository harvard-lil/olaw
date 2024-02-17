/**
 * @typedef {object} OpenLegalRagState
 * @property {{role: string, content: string}[]} history - Keeps track of "basic" chat history. To be fed back to the API with each exchange.
 * @property {?string} searchStatement - Latest `search_target` returned by the API (`/api/extract-search-statement`).
 * @property {?string} searchTarget - Latest `search_target` returned by the API (`/api/extract-search-statement`).
 * @property {object} searchResults - Latest output from `/api/search`.
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
};
