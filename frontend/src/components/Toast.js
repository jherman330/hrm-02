import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';

/**
 * Toast Context for app-wide notifications
 */
const ToastContext = createContext(null);

/**
 * Toast types with corresponding colors
 */
const TOAST_TYPES = {
  success: {
    background: 'rgba(39, 174, 96, 0.95)',
    icon: '✓',
  },
  error: {
    background: 'rgba(231, 76, 60, 0.95)',
    icon: '✕',
  },
  warning: {
    background: 'rgba(243, 156, 18, 0.95)',
    icon: '⚠',
  },
  info: {
    background: 'rgba(52, 152, 219, 0.95)',
    icon: 'ℹ',
  },
};

/**
 * Individual Toast Component
 */
function ToastItem({ toast, onRemove }) {
  const config = TOAST_TYPES[toast.type] || TOAST_TYPES.info;

  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, toast.duration || 4000);

    return () => clearTimeout(timer);
  }, [toast.id, toast.duration, onRemove]);

  return (
    <div
      style={{
        ...styles.toast,
        backgroundColor: config.background,
      }}
      onClick={() => onRemove(toast.id)}
    >
      <span style={styles.icon}>{config.icon}</span>
      <span style={styles.message}>{toast.message}</span>
    </div>
  );
}

/**
 * Toast Container Component
 */
function ToastContainer({ toasts, removeToast }) {
  if (toasts.length === 0) return null;

  return (
    <div style={styles.container}>
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
      ))}
    </div>
  );
}

/**
 * Toast Provider Component
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type, duration }]);
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const toast = {
    success: (message, duration) => addToast(message, 'success', duration),
    error: (message, duration) => addToast(message, 'error', duration),
    warning: (message, duration) => addToast(message, 'warning', duration),
    info: (message, duration) => addToast(message, 'info', duration),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

/**
 * Hook to access toast notifications
 */
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

const styles = {
  container: {
    position: 'fixed',
    top: '20px',
    right: '20px',
    zIndex: 9999,
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    maxWidth: '400px',
  },
  toast: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px 20px',
    borderRadius: '8px',
    color: '#fff',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
    cursor: 'pointer',
    animation: 'slideIn 0.3s ease-out',
    backdropFilter: 'blur(10px)',
  },
  icon: {
    fontSize: '1.2rem',
    fontWeight: 'bold',
  },
  message: {
    fontSize: '0.95rem',
    lineHeight: '1.4',
  },
};

// Add animation styles to document
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(styleSheet);
}

export default ToastContext;

