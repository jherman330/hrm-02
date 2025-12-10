import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTaskContext } from '../context/TaskContext';
import { useToast } from '../components/Toast';
import TaskItem from '../components/TaskItem';
import taskService, { ApiError } from '../services/taskService';

/**
 * TaskList page component.
 * Displays the list of tasks with API integration and error handling.
 */
function TaskList() {
  const { tasks, loading, setTasks, updateTask, deleteTask, setLoading, setError } = useTaskContext();
  const toast = useToast();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch tasks on mount
  useEffect(() => {
    async function fetchTasks() {
      setLoading(true);
      try {
        const data = await taskService.getTasks();
        setTasks(data);
      } catch (error) {
        const message = error instanceof ApiError 
          ? error.message 
          : 'Failed to load tasks';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    }
    
    fetchTasks();
  }, [setTasks, setLoading, setError, toast]);

  // Handle refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const data = await taskService.refreshCache();
      setTasks(data);
      toast.success('Tasks refreshed');
    } catch (error) {
      toast.error('Failed to refresh tasks');
    } finally {
      setIsRefreshing(false);
    }
  };

  // Handle task update
  const handleUpdate = async (taskId, updates) => {
    try {
      const updatedTask = await taskService.updateTask(taskId, updates);
      updateTask(updatedTask);
      toast.success('Task updated');
      return updatedTask;
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to update task';
      toast.error(message);
      throw error;
    }
  };

  // Handle task deletion
  const handleDelete = async (taskId) => {
    try {
      await taskService.deleteTask(taskId);
      deleteTask(taskId);
      toast.success('Task deleted');
    } catch (error) {
      toast.error(error.message || 'Failed to delete task');
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Task Manager</h1>
        <div style={styles.actions}>
          <button 
            onClick={handleRefresh} 
            style={styles.refreshButton}
            disabled={isRefreshing}
          >
            {isRefreshing ? '↻' : '⟳'} Refresh
          </button>
          <Link to="/tasks/new" style={styles.createButton}>
            + New Task
          </Link>
        </div>
      </header>

      {loading && !tasks.length ? (
        <div style={styles.loading}>
          <div style={styles.spinner}></div>
          Loading tasks...
        </div>
      ) : tasks.length === 0 ? (
        <div style={styles.empty}>
          <p>No tasks yet.</p>
          <Link to="/tasks/new" style={styles.link}>Create your first task</Link>
        </div>
      ) : (
        <div style={styles.taskList}>
          {tasks.map(task => (
            <TaskItem
              key={task.id}
              task={task}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '24px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '32px',
    flexWrap: 'wrap',
    gap: '16px',
  },
  title: {
    fontSize: '2rem',
    fontWeight: '600',
    color: '#fff',
    margin: 0,
  },
  actions: {
    display: 'flex',
    gap: '12px',
  },
  refreshButton: {
    backgroundColor: 'transparent',
    border: '1px solid rgba(255,255,255,0.3)',
    color: '#a0a0a0',
    padding: '12px 20px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  createButton: {
    backgroundColor: '#e94560',
    color: '#fff',
    padding: '12px 24px',
    borderRadius: '8px',
    textDecoration: 'none',
    fontWeight: '500',
    transition: 'background-color 0.2s',
  },
  loading: {
    textAlign: 'center',
    padding: '48px',
    color: '#a0a0a0',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
  },
  spinner: {
    width: '32px',
    height: '32px',
    border: '3px solid rgba(255,255,255,0.1)',
    borderTopColor: '#e94560',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  empty: {
    textAlign: 'center',
    padding: '48px',
    color: '#a0a0a0',
  },
  link: {
    color: '#e94560',
    textDecoration: 'none',
  },
  taskList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
};

// Add spinner animation
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(styleSheet);
}

export default TaskList;
