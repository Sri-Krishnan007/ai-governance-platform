import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import SubmitAction from './pages/SubmitAction';
import GovernanceCases from './pages/GovernanceCases';
import AuditLogs from './pages/AuditLogs';
import PolicySettings from './pages/PolicySettings';

// Temporary placeholder components for routes implemented in later phases
const Placeholder = ({ title }) => (
  <div className="glass-panel fade-in" style={{ padding: '40px', textAlign: 'center' }}>
    <h2 style={{ marginBottom: '12px' }}>{title}</h2>
    <p style={{ color: 'var(--text-secondary)' }}>
      This module is under development and will be implemented in subsequent phases.
    </p>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes inside Common Layout */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Dashboard */}
            <Route index element={<Dashboard />} />

            {/* Action Submission (Phase 5) */}
            <Route path="actions/submit" element={<SubmitAction />} />

            {/* Governance Case Management (Phase 12) */}
            <Route
              path="cases"
              element={
                <ProtectedRoute allowedRoles={['Governance Reviewer', 'Administrator']}>
                  <GovernanceCases />
                </ProtectedRoute>
              }
            />


            {/* Policy Management (Phase 8) */}
            <Route
              path="policies"
              element={
                <ProtectedRoute allowedRoles={['Administrator']}>
                  <PolicySettings />
                </ProtectedRoute>
              }
            />

            {/* Audit Logs (Phase 14) */}
            <Route
              path="audit"
              element={
                <ProtectedRoute allowedRoles={['Administrator']}>
                  <AuditLogs />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Fallback routing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
