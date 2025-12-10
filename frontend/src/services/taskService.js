/**
 * Task Service
 * Handles all task-related API operations with caching and error handling.
 */

import api, { ApiError } from './api';

// In-memory cache for tasks
let taskCache = {
  tasks: null,
  lastFetched: null,
  cacheDuration: 30000, // 30 seconds
};

/**
 * Check if cache is valid
 */
function isCacheValid() {
  if (!taskCache.tasks || !taskCache.lastFetched) {
    return false;
  }
  return Date.now() - taskCache.lastFetched < taskCache.cacheDuration;
}

/**
 * Invalidate cache
 */
function invalidateCache() {
  taskCache.tasks = null;
  taskCache.lastFetched = null;
}

/**
 * Update a single task in cache
 */
function updateTaskInCache(updatedTask) {
  if (taskCache.tasks) {
    taskCache.tasks = taskCache.tasks.map(task =>
      task.id === updatedTask.id ? updatedTask : task
    );
  }
}

/**
 * Add a task to cache
 */
function addTaskToCache(newTask) {
  if (taskCache.tasks) {
    taskCache.tasks = [newTask, ...taskCache.tasks];
  }
}

/**
 * Remove a task from cache
 */
function removeTaskFromCache(taskId) {
  if (taskCache.tasks) {
    taskCache.tasks = taskCache.tasks.filter(task => task.id !== taskId);
  }
}

/**
 * Task Service API
 */
const taskService = {
  /**
   * Get all tasks
   * Uses cache if available and valid
   */
  getTasks: async (options = {}) => {
    const { forceRefresh = false } = options;
    
    // Return cached data if valid and not forcing refresh
    if (!forceRefresh && isCacheValid()) {
      return taskCache.tasks;
    }
    
    try {
      const tasks = await api.get('/tasks');
      
      // Update cache
      taskCache.tasks = tasks;
      taskCache.lastFetched = Date.now();
      
      return tasks;
    } catch (error) {
      // Return stale cache if available on error
      if (taskCache.tasks && error instanceof ApiError) {
        console.warn('Using stale cache due to API error:', error.message);
        return taskCache.tasks;
      }
      throw error;
    }
  },

  /**
   * Get a single task by ID
   */
  getTask: async (taskId) => {
    // Try to find in cache first
    if (taskCache.tasks) {
      const cachedTask = taskCache.tasks.find(t => t.id === taskId);
      if (cachedTask) {
        return cachedTask;
      }
    }
    
    return api.get(`/tasks/${taskId}`);
  },

  /**
   * Create a new task
   */
  createTask: async (taskData) => {
    const newTask = await api.post('/tasks', taskData);
    
    // Update cache
    addTaskToCache(newTask);
    
    return newTask;
  },

  /**
   * Update an existing task
   */
  updateTask: async (taskId, taskData) => {
    const updatedTask = await api.put(`/tasks/${taskId}`, taskData);
    
    // Update cache
    updateTaskInCache(updatedTask);
    
    return updatedTask;
  },

  /**
   * Delete a task (soft delete by setting status to Deleted)
   */
  deleteTask: async (taskId) => {
    const result = await api.delete(`/tasks/${taskId}`);
    
    // Remove from cache
    removeTaskFromCache(taskId);
    
    return result;
  },

  /**
   * Get tasks with filters
   */
  getFilteredTasks: async (filters = {}) => {
    const { status, sort_by, sort_order } = filters;
    return api.get('/api/tasks/filter', { status, sort_by, sort_order });
  },

  /**
   * Force refresh cache
   */
  refreshCache: async () => {
    invalidateCache();
    return taskService.getTasks({ forceRefresh: true });
  },

  /**
   * Clear cache
   */
  clearCache: () => {
    invalidateCache();
  },
};

export default taskService;
export { ApiError };

