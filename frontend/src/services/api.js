/**
 * API Client Service
 * Centralized HTTP client with error handling, retry logic, and response transformation.
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5050';

// Default request configuration
const DEFAULT_CONFIG = {
  headers: {
    'Content-Type': 'application/json',
  },
};

// Retry configuration
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

/**
 * Custom API Error class for consistent error handling
 */
export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Sleep utility for retry delays
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Transform API response to consistent format
 */
function transformResponse(data) {
  if (data.success && data.data) {
    return data.data;
  }
  if (data.success === false && data.error) {
    throw new ApiError(data.error, 400, data);
  }
  return data;
}

/**
 * Core fetch wrapper with error handling and retry logic
 */
async function fetchWithRetry(url, options = {}, retries = 0) {
  const config = {
    ...DEFAULT_CONFIG,
    ...options,
    headers: {
      ...DEFAULT_CONFIG.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    // Handle non-OK responses
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let errorData = null;
      
      try {
        errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
      } catch {
        // Response is not JSON
      }
      
      // Retry on specific status codes
      if (RETRY_CONFIG.retryableStatuses.includes(response.status) && retries < RETRY_CONFIG.maxRetries) {
        await sleep(RETRY_CONFIG.retryDelay * (retries + 1));
        return fetchWithRetry(url, options, retries + 1);
      }
      
      throw new ApiError(errorMessage, response.status, errorData);
    }
    
    // Parse JSON response
    const data = await response.json();
    return transformResponse(data);
    
  } catch (error) {
    // Handle network errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      if (retries < RETRY_CONFIG.maxRetries) {
        await sleep(RETRY_CONFIG.retryDelay * (retries + 1));
        return fetchWithRetry(url, options, retries + 1);
      }
      throw new ApiError('Network error. Please check your connection.', 0);
    }
    
    // Re-throw API errors
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Handle other errors
    throw new ApiError(error.message || 'An unexpected error occurred', 0);
  }
}

/**
 * API Client with HTTP methods
 */
const api = {
  /**
   * GET request
   */
  get: async (endpoint, params = {}) => {
    const url = new URL(`${API_BASE_URL}${endpoint}`);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });
    return fetchWithRetry(url.toString(), { method: 'GET' });
  },

  /**
   * POST request
   */
  post: async (endpoint, data = {}) => {
    return fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * PUT request
   */
  put: async (endpoint, data = {}) => {
    return fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * DELETE request
   */
  delete: async (endpoint) => {
    return fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
    });
  },
};

export default api;

