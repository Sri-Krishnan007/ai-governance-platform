import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState(null);
  const { login, loading } = useAuth();
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get redirect path or default to Dashboard
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    
    if (!username.trim() || !password.trim()) {
      setLocalError("Please enter both username and password");
      return;
    }

    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setLocalError(err.message || "Failed to log in. Please check your credentials.");
    }
  };

  return (
    <div className="login-container">
      <div className="glass-panel login-card fade-in">
        <div className="login-header">
          <div className="login-logo">🛡️</div>
          <h1 className="login-title">Welcome Back</h1>
          <p className="login-subtitle">Sign in to Enterprise AI Governance Platform</p>
        </div>

        {localError && (
          <div className="login-error-alert">
            <span className="error-icon">⚠️</span>
            <span className="error-message">{localError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label className="input-label" htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              className="input-field"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input-field"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary login-submit-btn"
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="login-footer">
          <span>New to the platform? </span>
          <Link to="/register">Create an account</Link>
        </div>
      </div>

      <style>{`
        .login-container {
          min-height: 100vh;
          width: 100vw;
          display: flex;
          align-items: center;
          justify-content: center;
          background-color: var(--bg-primary);
          background-image: 
            radial-gradient(at 10% 10%, rgba(168, 85, 247, 0.15) 0px, transparent 40%),
            radial-gradient(at 90% 90%, rgba(6, 182, 212, 0.15) 0px, transparent 40%);
          padding: 20px;
        }

        .login-card {
          width: 100%;
          max-width: 440px;
          padding: 40px;
          border-radius: var(--border-radius-lg);
          text-align: center;
        }

        .login-header {
          margin-bottom: 32px;
        }

        .login-logo {
          font-size: 48px;
          margin-bottom: 16px;
        }

        .login-title {
          font-size: 28px;
          font-weight: 700;
          letter-spacing: -0.5px;
          color: var(--text-primary);
          margin-bottom: 8px;
        }

        .login-subtitle {
          font-size: 14px;
          color: var(--text-secondary);
        }

        .login-error-alert {
          background: var(--status-danger-bg);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: var(--border-radius-sm);
          padding: 12px 16px;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 12px;
          text-align: left;
        }

        .error-icon {
          font-size: 18px;
        }

        .error-message {
          font-size: 14px;
          color: var(--status-danger);
          font-weight: 500;
        }

        .login-form {
          margin-bottom: 24px;
        }

        .login-submit-btn {
          width: 100%;
          margin-top: 8px;
        }

        .login-footer {
          font-size: 14px;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
};

export default Login;
