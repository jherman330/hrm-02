import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTaskContext } from '../context/TaskContext';
import { useToast } from '../components/Toast';
import taskService, { ApiError } from '../services/taskService';

/**
 * TaskCreate page component.
 * Provides a form to create new tasks with API integration.
 */
function TaskCreate() {
  const navigate = useNavigate();
  const { addTask } = useTaskContext();
  const toast = useToast();
  
  const [formData, setFormData] = useState({
    title: '',
    due_date: '',
    comments: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) {
      toast.warning('Please fix the errors');
      return;
    }

    setSubmitting(true);
    
    try {
      const taskData = {
        title: formData.title.trim(),
        due_date: formData.due_date || null,
        comments: formData.comments.trim() || null,
      };
      
      const newTask = await taskService.createTask(taskData);
      addTask(newTask);
      toast.success('Task created successfully');
      navigate('/tasks');
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to create task';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <Link to="/tasks" style={styles.backLink}>
          ← Back to Tasks
        </Link>
        <h1 style={styles.title}>Create New Task</h1>
      </header>

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.formGroup}>
          <label htmlFor="title" style={styles.label}>
            Title <span style={styles.required}>*</span>
          </label>
          <input
            type="text"
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Enter task title"
            style={{
              ...styles.input,
              borderColor: errors.title ? '#e74c3c' : 'rgba(255, 255, 255, 0.2)',
            }}
            maxLength={255}
            disabled={submitting}
          />
          {errors.title && (
            <span style={styles.errorText}>{errors.title}</span>
          )}
        </div>

        <div style={styles.formGroup}>
          <label htmlFor="due_date" style={styles.label}>
            Due Date
          </label>
          <input
            type="datetime-local"
            id="due_date"
            name="due_date"
            value={formData.due_date}
            onChange={handleChange}
            style={styles.input}
            disabled={submitting}
          />
        </div>

        <div style={styles.formGroup}>
          <label htmlFor="comments" style={styles.label}>
            Comments
          </label>
          <textarea
            id="comments"
            name="comments"
            value={formData.comments}
            onChange={handleChange}
            placeholder="Add any notes or comments"
            style={styles.textarea}
            rows={4}
            maxLength={1000}
            disabled={submitting}
          />
        </div>

        <div style={styles.buttonGroup}>
          <Link to="/tasks" style={styles.cancelButton}>
            Cancel
          </Link>
          <button
            type="submit"
            style={{
              ...styles.submitButton,
              opacity: submitting ? 0.7 : 1,
            }}
            disabled={submitting}
          >
            {submitting ? (
              <>
                <span style={styles.buttonSpinner}></span>
                Creating...
              </>
            ) : (
              'Create Task'
            )}
          </button>
        </div>
      </form>
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
  form: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    padding: '24px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  formGroup: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    color: '#e0e0e0',
    fontWeight: '500',
  },
  required: {
    color: '#e94560',
  },
  input: {
    width: '100%',
    padding: '12px 16px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '1rem',
    outline: 'none',
    boxSizing: 'border-box',
  },
  textarea: {
    width: '100%',
    padding: '12px 16px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontSize: '1rem',
    outline: 'none',
    resize: 'vertical',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  },
  errorText: {
    color: '#e74c3c',
    fontSize: '0.8rem',
    marginTop: '4px',
    display: 'block',
  },
  buttonGroup: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'flex-end',
    marginTop: '24px',
  },
  cancelButton: {
    padding: '12px 24px',
    backgroundColor: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '8px',
    color: '#a0a0a0',
    textDecoration: 'none',
    fontWeight: '500',
  },
  submitButton: {
    padding: '12px 24px',
    backgroundColor: '#e94560',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    fontWeight: '500',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  buttonSpinner: {
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
};

export default TaskCreate;
