import React, { createContext, useContext, useReducer, useCallback } from 'react';

/**
 * Task Context for centralized state management.
 * Provides task data and update methods to all child components.
 */

// Initial state
const initialState = {
  tasks: [],
  loading: false,
  error: null,
};

// Action types
const ActionTypes = {
  SET_TASKS: 'SET_TASKS',
  ADD_TASK: 'ADD_TASK',
  UPDATE_TASK: 'UPDATE_TASK',
  DELETE_TASK: 'DELETE_TASK',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer function
function taskReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_TASKS:
      return {
        ...state,
        tasks: action.payload,
        loading: false,
        error: null,
      };
    
    case ActionTypes.ADD_TASK:
      return {
        ...state,
        tasks: [action.payload, ...state.tasks],
        loading: false,
      };
    
    case ActionTypes.UPDATE_TASK:
      return {
        ...state,
        tasks: state.tasks.map(task =>
          task.id === action.payload.id ? action.payload : task
        ),
        loading: false,
      };
    
    case ActionTypes.DELETE_TASK:
      return {
        ...state,
        tasks: state.tasks.filter(task => task.id !== action.payload),
        loading: false,
      };
    
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        loading: action.payload,
      };
    
    case ActionTypes.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    
    case ActionTypes.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    
    default:
      return state;
  }
}

// Create context
const TaskContext = createContext(null);

/**
 * TaskProvider component that wraps the application and provides task state.
 */
export function TaskProvider({ children }) {
  const [state, dispatch] = useReducer(taskReducer, initialState);

  // Action creators
  const setTasks = useCallback((tasks) => {
    dispatch({ type: ActionTypes.SET_TASKS, payload: tasks });
  }, []);

  const addTask = useCallback((task) => {
    dispatch({ type: ActionTypes.ADD_TASK, payload: task });
  }, []);

  const updateTask = useCallback((task) => {
    dispatch({ type: ActionTypes.UPDATE_TASK, payload: task });
  }, []);

  const deleteTask = useCallback((taskId) => {
    dispatch({ type: ActionTypes.DELETE_TASK, payload: taskId });
  }, []);

  const setLoading = useCallback((loading) => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: loading });
  }, []);

  const setError = useCallback((error) => {
    dispatch({ type: ActionTypes.SET_ERROR, payload: error });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: ActionTypes.CLEAR_ERROR });
  }, []);

  const value = {
    // State
    tasks: state.tasks,
    loading: state.loading,
    error: state.error,
    // Actions
    setTasks,
    addTask,
    updateTask,
    deleteTask,
    setLoading,
    setError,
    clearError,
  };

  return (
    <TaskContext.Provider value={value}>
      {children}
    </TaskContext.Provider>
  );
}

/**
 * Custom hook to access task context.
 * Must be used within a TaskProvider.
 */
export function useTaskContext() {
  const context = useContext(TaskContext);
  if (!context) {
    throw new Error('useTaskContext must be used within a TaskProvider');
  }
  return context;
}

export default TaskContext;

