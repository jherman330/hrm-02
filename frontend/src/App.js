import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { TaskProvider } from './context/TaskContext';
import router from './router';

/**
 * Root App component.
 * Serves as the main application entry point.
 * Integrates routing and centralized state management.
 */
function App() {
  return (
    <TaskProvider>
      <RouterProvider router={router} />
    </TaskProvider>
  );
}

export default App;

