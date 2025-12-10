import React, { useState, useRef, useEffect } from 'react';

/**
 * TaskItem Component
 * Displays individual task information with inline editing capabilities.
 */

const STATUS_OPTIONS = ['Open', 'In Progress', 'Blocked', 'Closed', 'Deleted'];

function TaskItem({ task, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    title: task.title,
    due_date: task.due_date ? formatDateForInput(task.due_date) : '',
    status: task.status,
    comments: task.comments || '',
  });
  const [errors, setErrors] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const titleInputRef = useRef(null);

  // Focus title input when entering edit mode
  useEffect(() => {
    if (isEditing && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [isEditing]);

  // Reset edit data when task changes
  useEffect(() => {
    setEditData({
      title: task.title,
      due_date: task.due_date ? formatDateForInput(task.due_date) : '',
      status: task.status,
      comments: task.comments || '',
    });
  }, [task]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!editData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;

    setIsSaving(true);
    try {
      const updates = {
        title: editData.title.trim(),
        due_date: editData.due_date || null,
        status: editData.status,
        comments: editData.comments.trim() || null,
      };
      await onUpdate(task.id, updates);
      setIsEditing(false);
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to save' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditData({
      title: task.title,
      due_date: task.due_date ? formatDateForInput(task.due_date) : '',
      status: task.status,
      comments: task.comments || '',
    });
    setErrors({});
    setIsEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const handleDelete = () => {
    if (window.confirm(`Delete "${task.title}"?`)) {
      onDelete(task.id);
    }
  };

  if (isEditing) {
    return (
      <div style={styles.card} role="form" aria-label="Edit task">
        {errors.submit && (
          <div style={styles.submitError}>{errors.submit}</div>
        )}
        
        <div style={styles.editGrid}>
          <div style={styles.formGroup}>
            <label htmlFor={`title-${task.id}`} style={styles.label}>
              Title <span style={styles.required}>*</span>
            </label>
            <input
              ref={titleInputRef}
              type="text"
              id={`title-${task.id}`}
              name="title"
              value={editData.title}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              style={{
                ...styles.input,
                borderColor: errors.title ? '#e74c3c' : 'rgba(255,255,255,0.2)',
              }}
              maxLength={255}
              disabled={isSaving}
              aria-invalid={!!errors.title}
              aria-describedby={errors.title ? `title-error-${task.id}` : undefined}
            />
            {errors.title && (
              <span id={`title-error-${task.id}`} style={styles.errorText}>
                {errors.title}
              </span>
            )}
          </div>

          <div style={styles.formGroup}>
            <label htmlFor={`status-${task.id}`} style={styles.label}>
              Status
            </label>
            <select
              id={`status-${task.id}`}
              name="status"
              value={editData.status}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              style={styles.select}
              disabled={isSaving}
            >
              {STATUS_OPTIONS.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label htmlFor={`due_date-${task.id}`} style={styles.label}>
              Due Date
            </label>
            <input
              type="datetime-local"
              id={`due_date-${task.id}`}
              name="due_date"
              value={editData.due_date}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              style={styles.input}
              disabled={isSaving}
            />
          </div>

          <div style={{ ...styles.formGroup, gridColumn: '1 / -1' }}>
            <label htmlFor={`comments-${task.id}`} style={styles.label}>
              Comments
            </label>
            <textarea
              id={`comments-${task.id}`}
              name="comments"
              value={editData.comments}
              onChange={handleChange}
              onKeyDown={(e) => {
                if (e.key === 'Escape') handleCancel();
              }}
              style={styles.textarea}
              rows={2}
              maxLength={1000}
              disabled={isSaving}
            />
          </div>
        </div>

        <div style={styles.editActions}>
          <button
            onClick={handleCancel}
            style={styles.cancelButton}
            disabled={isSaving}
            type="button"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={{
              ...styles.saveButton,
              opacity: isSaving ? 0.7 : 1,
            }}
            disabled={isSaving}
            type="button"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      style={styles.card}
      role="article"
      aria-label={`Task: ${task.title}`}
    >
      <div style={styles.taskHeader}>
        <h3 style={styles.taskTitle}>{task.title}</h3>
        <div style={styles.taskActions}>
          <span style={{
            ...styles.status,
            backgroundColor: getStatusColor(task.status),
          }}>
            {task.status}
          </span>
          <button
            onClick={() => setIsEditing(true)}
            style={styles.editButton}
            title="Edit task"
            aria-label={`Edit ${task.title}`}
          >
            ✎
          </button>
          <button
            onClick={handleDelete}
            style={styles.deleteButton}
            title="Delete task"
            aria-label={`Delete ${task.title}`}
          >
            ×
          </button>
        </div>
      </div>
      
      {task.due_date && (
        <p style={styles.dueDate}>
          📅 Due: {new Date(task.due_date).toLocaleDateString()}
        </p>
      )}
      
      {task.comments && (
        <p style={styles.comments}>{task.comments}</p>
      )}
      
      <div style={styles.meta}>
        Created: {new Date(task.created_at).toLocaleDateString()}
        {task.updated_at !== task.created_at && (
          <> · Updated: {new Date(task.updated_at).toLocaleDateString()}</>
        )}
      </div>
    </div>
  );
}

function formatDateForInput(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toISOString().slice(0, 16);
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
  card: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    padding: '20px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  taskHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '8px',
    gap: '12px',
  },
  taskTitle: {
    fontSize: '1.1rem',
    fontWeight: '500',
    color: '#fff',
    margin: 0,
    flex: 1,
  },
  taskActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexShrink: 0,
  },
  status: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '500',
    color: '#fff',
  },
  editButton: {
    background: 'transparent',
    border: 'none',
    color: '#a0a0a0',
    fontSize: '1.1rem',
    cursor: 'pointer',
    padding: '4px 8px',
    borderRadius: '4px',
    transition: 'color 0.2s, background 0.2s',
  },
  deleteButton: {
    background: 'transparent',
    border: 'none',
    color: '#a0a0a0',
    fontSize: '1.5rem',
    cursor: 'pointer',
    padding: '0 4px',
    lineHeight: 1,
    transition: 'color 0.2s',
  },
  dueDate: {
    fontSize: '0.875rem',
    color: '#a0a0a0',
    margin: '8px 0',
  },
  comments: {
    fontSize: '0.875rem',
    color: '#c0c0c0',
    margin: '8px 0',
  },
  meta: {
    fontSize: '0.75rem',
    color: '#666',
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(255,255,255,0.05)',
  },
  // Edit mode styles
  editGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '0.8rem',
    color: '#a0a0a0',
    fontWeight: '500',
  },
  required: {
    color: '#e94560',
  },
  input: {
    padding: '10px 12px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '6px',
    color: '#fff',
    fontSize: '0.9rem',
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box',
  },
  select: {
    padding: '10px 12px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '6px',
    color: '#fff',
    fontSize: '0.9rem',
    outline: 'none',
    cursor: 'pointer',
  },
  textarea: {
    padding: '10px 12px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '6px',
    color: '#fff',
    fontSize: '0.9rem',
    outline: 'none',
    resize: 'vertical',
    fontFamily: 'inherit',
    width: '100%',
    boxSizing: 'border-box',
  },
  errorText: {
    color: '#e74c3c',
    fontSize: '0.75rem',
  },
  submitError: {
    backgroundColor: 'rgba(231, 76, 60, 0.2)',
    border: '1px solid #e74c3c',
    color: '#e74c3c',
    padding: '10px',
    borderRadius: '6px',
    marginBottom: '16px',
    fontSize: '0.85rem',
  },
  editActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
  },
  cancelButton: {
    padding: '8px 16px',
    backgroundColor: 'transparent',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    borderRadius: '6px',
    color: '#a0a0a0',
    cursor: 'pointer',
    fontSize: '0.85rem',
  },
  saveButton: {
    padding: '8px 20px',
    backgroundColor: '#27ae60',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: '500',
  },
};

export default TaskItem;

