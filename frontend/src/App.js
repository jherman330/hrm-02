import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { TaskProvider } from './context/TaskContext';
import { ToastProvider } from './components/Toast';
import router from './router';

/**
 * Root App component.
 * Serves as the main application entry point.
 * Integrates routing, state management, and toast notifications.
 */
function App() {
  return (
    <ToastProvider>
      <TaskProvider>
        <RouterProvider router={router} />
      </TaskProvider>
    </ToastProvider>
  );
}

export default App;
