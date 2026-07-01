import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { user } = useAuth();
  
  const roleName = user?.role?.name || 'Employee';

  // Navigation items mapping (some items shown depending on role)
  const navItems = [
    { to: '/', label: 'Dashboard', icon: '📊', roles: ['Employee', 'Governance Reviewer', 'Administrator'] },
    { to: '/actions/submit', label: 'Submit Action', icon: '⚡', roles: ['Employee', 'Administrator'] },
    { to: '/cases', label: 'Governance Cases', icon: '🛡️', roles: ['Governance Reviewer', 'Administrator'] },
    { to: '/policies', label: 'Policy Settings', icon: '📜', roles: ['Administrator'] },
    { to: '/audit', label: 'Audit Logs', icon: '📝', roles: ['Administrator'] },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-icon">🛡️</span>
        <span className="brand-name">Aivar Gov</span>
      </div>
      
      <div className="user-short-profile">
        <div className="user-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</div>
        <div className="user-meta">
          <div className="user-meta-name">{user?.username}</div>
          <span className="badge badge-info user-role-badge">{roleName}</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems
          .filter(item => item.roles.includes(roleName))
          .map((item, index) => (
            <NavLink
              key={index}
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}
            >
              <span className="nav-item-icon">{item.icon}</span>
              <span className="nav-item-label">{item.label}</span>
            </NavLink>
          ))}
      </nav>

      <style>{`
        .sidebar {
          width: var(--sidebar-width);
          background: var(--bg-secondary);
          border-right: 1px solid var(--glass-border);
          position: fixed;
          top: 0;
          bottom: 0;
          left: 0;
          z-index: 100;
          display: flex;
          flex-direction: column;
          padding: 24px 16px;
        }

        .sidebar-brand {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 32px;
          padding-left: 8px;
        }

        .brand-icon {
          font-size: 24px;
        }

        .brand-name {
          font-size: 20px;
          font-weight: 700;
          letter-spacing: 0.5px;
          background: var(--accent-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .user-short-profile {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid var(--glass-border);
          border-radius: var(--border-radius-md);
          margin-bottom: 24px;
        }

        .user-avatar {
          width: 40px;
          height: 40px;
          border-radius: var(--border-radius-sm);
          background: var(--accent-gradient);
          color: #fff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 16px;
          box-shadow: 0 4px 10px rgba(168, 85, 247, 0.2);
        }

        .user-meta {
          display: flex;
          flex-direction: column;
          gap: 2px;
          overflow: hidden;
        }

        .user-meta-name {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
        }

        .user-role-badge {
          font-size: 9px;
          padding: 2px 6px;
          width: fit-content;
        }

        .sidebar-nav {
          display: flex;
          flex-direction: column;
          gap: 6px;
          flex: 1;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border-radius: var(--border-radius-sm);
          color: var(--text-secondary);
          font-weight: 500;
          transition: var(--transition-smooth);
        }

        .nav-item:hover {
          background: rgba(255, 255, 255, 0.03);
          color: var(--text-primary);
        }

        .nav-item-active {
          background: rgba(168, 85, 247, 0.08) !important;
          border: 1px solid rgba(168, 85, 247, 0.2);
          color: var(--accent-purple) !important;
          font-weight: 600;
        }

        .nav-item-icon {
          font-size: 18px;
        }
      `}</style>
    </aside>
  );
};

export default Sidebar;
