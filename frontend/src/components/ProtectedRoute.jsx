import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        color: 'var(--text-secondary)'
      }}>
        <div style={{
          fontSize: '18px',
          fontWeight: '500',
          animation: 'pulse 1.5s infinite alternate'
        }}>
          Verifying secure session...
        </div>
        <style>{`
          @keyframes pulse {
            from { opacity: 0.5; }
            to { opacity: 1; }
          }
        `}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to login page and save the attempted URL
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if role restriction applies
  if (allowedRoles && (!user.role || !allowedRoles.includes(user.role.name))) {
    console.warn(`Access denied. User role '${user.role?.name}' not in allowed roles:`, allowedRoles);
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
