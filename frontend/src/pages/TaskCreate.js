import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTaskContext } from '../context/TaskContext';

/**
 * TaskCreate page component.
 * Provides a form to create new tasks.
 */
function TaskCreate() {
  const navigate = useNavigate();
  const { addTask, setError } = useTaskContext();
  
  const [formData, setFormData] = useState({
    title: '',
    due_date: '',
    comments: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    setSubmitting(true);
    
    try {
      // TODO: Replace with actual API call in service layer
      const newTask = {
        id: Date.now().toString(), // Temporary ID
        title: formData.title.trim(),
        due_date: formData.due_date || null,
        comments: formData.comments.trim() || null,
        status: 'Open',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      addTask(newTask);
      navigate('/tasks');
    } catch (error) {
      setError('Failed to create task');
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
            style={styles.input}
            maxLength={255}
            required
          />
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
          />
        </div>

        <div style={styles.buttonGroup}>
          <Link to="/tasks" style={styles.cancelButton}>
            Cancel
          </Link>
          <button
            type="submit"
            style={styles.submitButton}
            disabled={submitting}
          >
            {submitting ? 'Creating...' : 'Create Task'}
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
  },
};

export default TaskCreate;

