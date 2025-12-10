import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import TaskList from '../pages/TaskList';
import TaskCreate from '../pages/TaskCreate';

/**
 * Application routing configuration.
 * Defines routes for task list and task creation views.
 */
const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/tasks" replace />,
  },
  {
    path: '/tasks',
    element: <TaskList />,
  },
  {
    path: '/tasks/new',
    element: <TaskCreate />,
  },
  {
    path: '*',
    element: <Navigate to="/tasks" replace />,
  },
]);

export default router;

