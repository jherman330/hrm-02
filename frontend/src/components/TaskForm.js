import React, { useState, useRef, useEffect } from 'react';

/**
 * TaskForm Component
 * Reusable form for creating new tasks with validation and accessibility.
 */

const INITIAL_FORM_DATA = {
  title: '',
  due_date: '',
  comments: '',
};

function TaskForm({ onSubmit, onCancel, isSubmitting = false }) {
  const [formData, setFormData] = useState(INITIAL_FORM_DATA);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const titleInputRef = useRef(null);

  // Focus title input on mount
  useEffect(() => {
    if (titleInputRef.current) {
      titleInputRef.current.focus();
    }
  }, []);

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

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
    // Validate on blur
    validateField(name, formData[name]);
  };

  const validateField = (name, value) => {
    let error = null;
    
    switch (name) {
      case 'title':
        if (!value.trim()) {
          error = 'Title is required';
        } else if (value.trim().length < 2) {
          error = 'Title must be at least 2 characters';
        } else if (value.length > 255) {
          error = 'Title must be less than 255 characters';
        }
        break;
      case 'comments':
        if (value.length > 1000) {
          error = 'Comments must be less than 1000 characters';
        }
        break;
      default:
        break;
    }
    
    setErrors(prev => ({ ...prev, [name]: error }));
    return !error;
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    } else if (formData.title.trim().length < 2) {
      newErrors.title = 'Title must be at least 2 characters';
    }
    
    if (formData.comments.length > 1000) {
      newErrors.comments = 'Comments must be less than 1000 characters';
    }
    
    setErrors(newErrors);
    setTouched({ title: true, due_date: true, comments: true });
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) {
      // Focus first error field
      if (errors.title && titleInputRef.current) {
        titleInputRef.current.focus();
      }
      return;
    }

    const taskData = {
      title: formData.title.trim(),
      due_date: formData.due_date || null,
      comments: formData.comments.trim() || null,
    };

    const success = await onSubmit(taskData);
    
    // Reset form on success
    if (success) {
      resetForm();
    }
  };

  const resetForm = () => {
    setFormData(INITIAL_FORM_DATA);
    setErrors({});
    setTouched({});
    if (titleInputRef.current) {
      titleInputRef.current.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && onCancel) {
      onCancel();
    }
  };

  const handleCancel = () => {
    resetForm();
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      style={styles.form}
      onKeyDown={handleKeyDown}
      aria-label="Create new task"
      noValidate
    >
      <div style={styles.formGroup}>
        <label htmlFor="task-title" style={styles.label}>
          Title <span style={styles.required}>*</span>
        </label>
        <input
          ref={titleInputRef}
          type="text"
          id="task-title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="Enter task title"
          style={{
            ...styles.input,
            borderColor: errors.title && touched.title ? '#e74c3c' : 'rgba(255, 255, 255, 0.2)',
          }}
          maxLength={255}
          disabled={isSubmitting}
          aria-required="true"
          aria-invalid={!!(errors.title && touched.title)}
          aria-describedby={errors.title ? 'title-error' : 'title-hint'}
          autoComplete="off"
        />
        {errors.title && touched.title ? (
          <span id="title-error" style={styles.errorText} role="alert">
            {errors.title}
          </span>
        ) : (
          <span id="title-hint" style={styles.hint}>
            Required. Brief description of the task.
          </span>
        )}
      </div>

      <div style={styles.formGroup}>
        <label htmlFor="task-due-date" style={styles.label}>
          Due Date
        </label>
        <input
          type="datetime-local"
          id="task-due-date"
          name="due_date"
          value={formData.due_date}
          onChange={handleChange}
          style={styles.input}
          disabled={isSubmitting}
          aria-describedby="due-date-hint"
        />
        <span id="due-date-hint" style={styles.hint}>
          Optional. When should this task be completed?
        </span>
      </div>

      <div style={styles.formGroup}>
        <label htmlFor="task-comments" style={styles.label}>
          Comments
        </label>
        <textarea
          id="task-comments"
          name="comments"
          value={formData.comments}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="Add any notes or comments"
          style={{
            ...styles.textarea,
            borderColor: errors.comments && touched.comments ? '#e74c3c' : 'rgba(255, 255, 255, 0.2)',
          }}
          rows={4}
          maxLength={1000}
          disabled={isSubmitting}
          aria-invalid={!!(errors.comments && touched.comments)}
          aria-describedby={errors.comments ? 'comments-error' : 'comments-hint'}
        />
        {errors.comments && touched.comments ? (
          <span id="comments-error" style={styles.errorText} role="alert">
            {errors.comments}
          </span>
        ) : (
          <span id="comments-hint" style={styles.hint}>
            Optional. {1000 - formData.comments.length} characters remaining.
          </span>
        )}
      </div>

      <div style={styles.buttonGroup}>
        {onCancel && (
          <button
            type="button"
            onClick={handleCancel}
            style={styles.cancelButton}
            disabled={isSubmitting}
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          onClick={resetForm}
          style={styles.resetButton}
          disabled={isSubmitting}
          title="Clear form"
        >
          Reset
        </button>
        <button
          type="submit"
          style={{
            ...styles.submitButton,
            opacity: isSubmitting ? 0.7 : 1,
          }}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span style={styles.buttonSpinner} aria-hidden="true"></span>
              Creating...
            </>
          ) : (
            'Create Task'
          )}
        </button>
      </div>
    </form>
  );
}

const styles = {
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
    transition: 'border-color 0.2s',
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
    transition: 'border-color 0.2s',
  },
  errorText: {
    color: '#e74c3c',
    fontSize: '0.8rem',
    marginTop: '6px',
    display: 'block',
  },
  hint: {
    color: '#666',
    fontSize: '0.75rem',
    marginTop: '6px',
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
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'border-color 0.2s',
  },
  resetButton: {
    padding: '12px 20px',
    backgroundColor: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#666',
    fontWeight: '500',
    cursor: 'pointer',
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
    transition: 'background-color 0.2s',
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

export default TaskForm;

