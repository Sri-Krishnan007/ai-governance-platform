import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const Navbar = () => {
  const { user, logout } = useAuth();
  const [dbStatus, setDbStatus] = useState('checking');
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);

  const fetchNotifications = async () => {
    if (!user) return;
    try {
      const res = await api.get('/notifications');
      setNotifications(res.data);
    } catch (err) {
      console.error('Failed to retrieve user notifications:', err);
    }
  };

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.get('/health');
        if (res.data.database === 'connected') {
          setDbStatus('connected');
        } else {
          setDbStatus('disconnected');
        }
      } catch (err) {
        setDbStatus('error');
      }
    };

    checkHealth();
    const dbInterval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(dbInterval);
  }, []);

  useEffect(() => {
    if (user) {
      fetchNotifications();
      const notesInterval = setInterval(fetchNotifications, 10000); // Check every 10s
      return () => clearInterval(notesInterval);
    }
  }, [user]);

  // Close notifications dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAsRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`);
      setNotifications(prev =>
        prev.map(note => note.id === id ? { ...note, read: true } : note)
      );
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications(prev =>
        prev.map(note => ({ ...note, read: true }))
      );
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="navbar">
      <div className="navbar-left">
        <h2 className="navbar-title">Governance Engine Dashboard</h2>
      </div>

      <div className="navbar-right">
        {/* Database Health Badge */}
        <div className="db-status-container">
          <span className="db-status-label">DB Status:</span>
          {dbStatus === 'connected' && (
            <span className="badge badge-success db-status-badge">● Online</span>
          )}
          {dbStatus === 'disconnected' && (
            <span className="badge badge-danger db-status-badge">● Offline</span>
          )}
          {dbStatus === 'checking' && (
            <span className="badge badge-warning db-status-badge">● Checking</span>
          )}
          {dbStatus === 'error' && (
            <span className="badge badge-danger db-status-badge">● Connection Error</span>
          )}
        </div>

        <div className="navbar-divider"></div>

        {/* Notifications Icon and Dropdown */}
        {user && (
          <div className="notifications-container" ref={dropdownRef}>
            <button
              className="notifications-bell-btn"
              onClick={() => setShowNotifications(!showNotifications)}
              title="View notifications"
            >
              🔔
              {unreadCount > 0 && (
                <span className="notifications-badge">{unreadCount}</span>
              )}
            </button>

            {showNotifications && (
              <div className="notifications-dropdown glass-panel">
                <div className="notifications-header">
                  <h4 className="notifications-title">Notifications</h4>
                  {unreadCount > 0 && (
                    <button className="mark-all-read-btn" onClick={handleMarkAllAsRead}>
                      Mark all read ✓
                    </button>
                  )}
                </div>

                <div className="notifications-list">
                  {notifications.length === 0 ? (
                    <div className="notifications-empty">No notifications yet.</div>
                  ) : (
                    notifications.map((note) => (
                      <div
                        key={note.id}
                        onClick={() => !note.read && handleMarkAsRead(note.id)}
                        className={`notification-item ${note.read ? 'read' : 'unread'} ${note.notification_type.toLowerCase()}`}
                      >
                        <div className="notification-item-header">
                          <strong className="notification-item-title">{note.title}</strong>
                          {!note.read && <span className="unread-dot"></span>}
                        </div>
                        <p className="notification-item-message">{note.message}</p>
                        <span className="notification-item-time">
                          {new Date(note.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="navbar-divider"></div>

        {/* User Info & Logout Button */}
        <div className="navbar-user-info">
          <span className="navbar-username">{user?.username}</span>
          <button className="btn btn-secondary btn-sm logout-btn" onClick={logout}>
            Logout 🚪
          </button>
        </div>
      </div>

      <style>{`
        .navbar {
          height: var(--navbar-height);
          background: var(--glass-bg);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border-bottom: 1px solid var(--glass-border);
          position: sticky;
          top: 0;
          right: 0;
          left: 0;
          z-index: 90;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 32px;
        }

        .navbar-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary);
          letter-spacing: -0.2px;
          margin: 0;
        }

        .navbar-right {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .db-status-container {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .db-status-label {
          font-size: 13px;
          color: var(--text-secondary);
        }

        .db-status-badge {
          font-size: 11px;
          padding: 3px 10px;
          font-weight: 500;
        }

        .navbar-divider {
          width: 1px;
          height: 24px;
          background: var(--glass-border);
        }

        .notifications-container {
          position: relative;
        }

        .notifications-bell-btn {
          background: none;
          border: none;
          cursor: pointer;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 8px;
          font-size: 16px;
          border-radius: 50%;
          transition: background 0.2s ease;
        }

        .notifications-bell-btn:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .notifications-badge {
          position: absolute;
          top: -2px;
          right: -2px;
          background: var(--status-danger);
          color: #fff;
          font-size: 9px;
          font-weight: bold;
          border-radius: 50%;
          min-width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0 3px;
          border: 1px solid rgba(0,0,0,0.5);
        }

        .notifications-dropdown {
          position: absolute;
          top: calc(100% + 12px);
          right: 0;
          width: 340px;
          max-height: 420px;
          display: flex;
          flex-direction: column;
          z-index: 100;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
          animation: slideIn 0.2s ease;
        }

        @keyframes slideIn {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .notifications-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 14px;
          border-bottom: 1px solid var(--glass-border);
        }

        .notifications-title {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .mark-all-read-btn {
          background: none;
          border: none;
          color: var(--accent-cyan);
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          padding: 0;
          transition: opacity 0.2s;
        }

        .mark-all-read-btn:hover {
          opacity: 0.8;
        }

        .notifications-list {
          overflow-y: auto;
          max-height: 350px;
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .notifications-empty {
          padding: 24px;
          text-align: center;
          color: var(--text-muted);
          font-size: 13.5px;
        }

        .notification-item {
          padding: 10px 12px;
          border-radius: var(--border-radius-sm);
          font-size: 12.5px;
          transition: all 0.2s ease;
          display: flex;
          flex-direction: column;
          gap: 3px;
          border-left: 3px solid transparent;
        }

        .notification-item.unread {
          background: rgba(255, 255, 255, 0.04);
          cursor: pointer;
        }

        .notification-item.unread:hover {
          background: rgba(255, 255, 255, 0.08);
        }

        .notification-item.read {
          background: rgba(255, 255, 255, 0.01);
          opacity: 0.65;
        }

        .notification-item.confirmation_required,
        .notification-item.policy_violations {
          border-left-color: var(--status-warning);
        }

        .notification-item.escalated_case,
        .notification-item.security_alerts {
          border-left-color: var(--status-danger);
        }

        .notification-item.case_approved {
          border-left-color: var(--status-success);
        }

        .notification-item.case_rejected {
          border-left-color: var(--status-danger);
        }

        .notification-item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .notification-item-title {
          color: var(--text-primary);
          font-weight: 600;
        }

        .unread-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--accent-cyan);
        }

        .notification-item-message {
          margin: 0;
          color: var(--text-secondary);
          line-height: 1.4;
          font-size: 12px;
        }

        .notification-item-time {
          font-size: 9.5px;
          color: var(--text-muted);
          text-align: right;
          margin-top: 2px;
        }

        .navbar-user-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .navbar-username {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-secondary);
        }

        .logout-btn {
          padding: 6px 12px !important;
          font-size: 13px !important;
          border-radius: var(--border-radius-sm) !important;
        }
      `}</style>
    </header>
  );
};

export default Navbar;

