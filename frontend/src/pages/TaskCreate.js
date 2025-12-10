import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTaskContext } from '../context/TaskContext';
import { useToast } from '../components/Toast';
import TaskForm from '../components/TaskForm';
import taskService, { ApiError } from '../services/taskService';

/**
 * TaskCreate page component.
 * Provides a page wrapper for the TaskForm component.
 */
function TaskCreate() {
  const navigate = useNavigate();
  const { addTask } = useTaskContext();
  const toast = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (taskData) => {
    setIsSubmitting(true);
    
    try {
      const newTask = await taskService.createTask(taskData);
      addTask(newTask);
      toast.success('Task created successfully');
      navigate('/tasks');
      return true;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to create task';
      toast.error(message);
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate('/tasks');
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <Link to="/tasks" style={styles.backLink}>
          ← Back to Tasks
        </Link>
        <h1 style={styles.title}>Create New Task</h1>
      </header>

      <TaskForm
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}

const styles = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '24px',
  },
  header: {
    marginBottom: '32px',
  },
  backLink: {
    color: '#a0a0a0',
    textDecoration: 'none',
    fontSize: '0.875rem',
    display: 'inline-block',
    marginBottom: '16px',
  },
  title: {
    fontSize: '2rem',
    fontWeight: '600',
    color: '#fff',
    margin: 0,
  },
};

export default TaskCreate;
