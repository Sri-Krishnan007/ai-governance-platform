import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [roleId, setRoleId] = useState('1'); // Defaults to '1' (Employee)
  const [localError, setLocalError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  const { register, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    setSuccess(false);

    if (!username.trim() || !email.trim() || !password.trim()) {
      setLocalError("All fields are required");
      return;
    }

    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters long");
      return;
    }

    try {
      await register(username, email, password, roleId);
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000); // Redirect after 2 seconds
    } catch (err) {
      setLocalError(err.message || "Failed to create account. Try again.");
    }
  };

  return (
    <div className="register-container">
      <div className="glass-panel register-card fade-in">
        <div className="register-header">
          <div className="register-logo">🛡️</div>
          <h1 className="register-title">Create Account</h1>
          <p className="register-subtitle">Register to evaluate and manage AI operations</p>
        </div>

        {localError && (
          <div className="register-alert register-alert-danger">
            <span className="alert-icon">⚠️</span>
            <span className="alert-message">{localError}</span>
          </div>
        )}

        {success && (
          <div className="register-alert register-alert-success">
            <span className="alert-icon">✅</span>
            <span className="alert-message">Registration successful! Redirecting to sign in...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="register-form">
          <div className="input-group">
            <label className="input-label" htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              className="input-field"
              placeholder="johndoe"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading || success}
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              className="input-field"
              placeholder="john@enterprise.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading || success}
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
              disabled={loading || success}
            />
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="role">Assign Security Role</label>
            <select
              id="role"
              className="select-field"
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              disabled={loading || success}
            >
              <option value="1">Employee (Submit Actions)</option>
              <option value="2">Governance Reviewer (Approve/Reject Cases)</option>
              <option value="3">Administrator (Full Access)</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary register-submit-btn"
            disabled={loading || success}
          >
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div className="register-footer">
          <span>Already have an account? </span>
          <Link to="/login">Sign in</Link>
        </div>
      </div>

      <style>{`
        .register-container {
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

        .register-card {
          width: 100%;
          max-width: 460px;
          padding: 40px;
          border-radius: var(--border-radius-lg);
          text-align: center;
        }

        .register-header {
          margin-bottom: 28px;
        }

        .register-logo {
          font-size: 48px;
          margin-bottom: 12px;
        }

        .register-title {
          font-size: 28px;
          font-weight: 700;
          letter-spacing: -0.5px;
          color: var(--text-primary);
          margin-bottom: 8px;
        }

        .register-subtitle {
          font-size: 14px;
          color: var(--text-secondary);
        }

        .register-alert {
          border-radius: var(--border-radius-sm);
          padding: 12px 16px;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 12px;
          text-align: left;
        }
        
        .register-alert-danger {
          background: var(--status-danger-bg);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: var(--status-danger);
        }
        
        .register-alert-success {
          background: var(--status-success-bg);
          border: 1px solid rgba(16, 185, 129, 0.2);
          color: var(--status-success);
        }

        .alert-icon {
          font-size: 18px;
        }

        .alert-message {
          font-size: 14px;
          font-weight: 500;
        }

        .register-form {
          margin-bottom: 24px;
        }

        .register-submit-btn {
          width: 100%;
          margin-top: 8px;
        }

        .register-footer {
          font-size: 14px;
          color: var(--text-secondary);
        }
      `}</style>
    </div>
  );
};

export default Register;
