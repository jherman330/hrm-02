import React from 'react';
import { Link } from 'react-router-dom';
import { useTaskContext } from '../context/TaskContext';

/**
 * TaskList page component.
 * Displays the list of tasks and provides navigation to create new tasks.
 */
function TaskList() {
  const { tasks, loading, error } = useTaskContext();

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Task Manager</h1>
        <Link to="/tasks/new" style={styles.createButton}>
          + New Task
        </Link>
      </header>

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={styles.loading}>Loading tasks...</div>
      ) : tasks.length === 0 ? (
        <div style={styles.empty}>
          <p>No tasks yet.</p>
          <Link to="/tasks/new" style={styles.link}>Create your first task</Link>
        </div>
      ) : (
        <div style={styles.taskList}>
          {tasks.map(task => (
            <div key={task.id} style={styles.taskCard}>
              <div style={styles.taskHeader}>
                <h3 style={styles.taskTitle}>{task.title}</h3>
                <span style={{
                  ...styles.status,
                  backgroundColor: getStatusColor(task.status)
                }}>
                  {task.status}
                </span>
              </div>
              {task.due_date && (
                <p style={styles.dueDate}>
                  Due: {new Date(task.due_date).toLocaleDateString()}
                </p>
              )}
              {task.comments && (
                <p style={styles.comments}>{task.comments}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function getStatusColor(status) {
  const colors = {
    'Open': '#3498db',
    'In Progress': '#f39c12',
    'Blocked': '#e74c3c',
    'Closed': '#27ae60',
    'Deleted': '#95a5a6',
  };
  return colors[status] || '#7f8c8d';
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
  },
  title: {
    fontSize: '2rem',
    fontWeight: '600',
    color: '#fff',
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
  error: {
    backgroundColor: 'rgba(231, 76, 60, 0.2)',
    border: '1px solid #e74c3c',
    color: '#e74c3c',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '16px',
  },
  loading: {
    textAlign: 'center',
    padding: '48px',
    color: '#a0a0a0',
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
  taskCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  taskHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '8px',
  },
  taskTitle: {
    fontSize: '1.1rem',
    fontWeight: '500',
    color: '#fff',
    margin: 0,
  },
  status: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '500',
    color: '#fff',
  },
  dueDate: {
    fontSize: '0.875rem',
    color: '#a0a0a0',
    margin: '8px 0',
  },
  comments: {
    fontSize: '0.875rem',
    color: '#c0c0c0',
    margin: 0,
  },
};

export default TaskList;

