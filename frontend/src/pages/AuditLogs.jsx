import React, { useState, useEffect } from 'react';
import api from '../services/api';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/audit');
      setLogs(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to retrieve system audit logs.');
    } finally {
      setLoading(false);
    }
  };

  const getEventBadgeClass = (eventType) => {
    if (eventType.includes('APPROVAL') || eventType.includes('APPROVED')) {
      return 'badge-success';
    }
    if (eventType.includes('REJECT') || eventType.includes('REJECTED')) {
      return 'badge-danger';
    }
    if (eventType.includes('CLARIFICATION') || eventType.includes('PENDING')) {
      return 'badge-warning';
    }
    if (eventType.includes('SUBMISSION')) {
      return 'badge-info';
    }
    return 'badge-secondary';
  };

  const filteredLogs = logs.filter((log) => {
    const query = searchQuery.toLowerCase();
    const username = log.user?.username?.toLowerCase() || '';
    const eventType = log.event_type.toLowerCase();
    const details = log.details.toLowerCase();
    const reqText = log.action?.natural_language_request?.toLowerCase() || '';
    
    return username.includes(query) ||
           eventType.includes(query) ||
           details.includes(query) ||
           reqText.includes(query);
  });

  return (
    <div className="audit-logs-container fade-in">
      <div className="audit-header" style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', width: 'fit-content' }}>
          Immutable Audit Trail
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Real-time, read-only ledger capturing user requests, LLMintent evaluations, policy alerts, risk calculations, and manual review decisions.
        </p>
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: 'var(--status-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--border-radius-sm)', color: '#ef4444', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Search & Actions Panel */}
      <div className="glass-panel" style={{ padding: '16px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '260px' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search logs by event, user details, action requests..."
            style={{
              width: '100%',
              padding: '10px 14px',
              background: 'rgba(0, 0, 0, 0.2)',
              border: '1px solid var(--glass-border)',
              borderRadius: 'var(--border-radius-sm)',
              color: '#fff',
              fontSize: '14px',
              outline: 'none',
              transition: 'var(--transition-smooth)'
            }}
          />
        </div>
        <button
          onClick={fetchLogs}
          className="btn-tab"
          style={{
            padding: '10px 20px',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--glass-border)',
            borderRadius: 'var(--border-radius-sm)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          🔄 Refresh Log Ledger
        </button>
      </div>

      {/* Logs Table Container */}
      <div className="glass-panel" style={{ overflowX: 'auto', padding: '0px' }}>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            Retrieving audit ledger...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            📭 No audit entries found.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '800px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--glass-border)', background: 'rgba(255, 255, 255, 0.01)' }}>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '600', textTransform: 'uppercase' }}>Timestamp</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '600', textTransform: 'uppercase' }}>Event Type</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '600', textTransform: 'uppercase' }}>Actor</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '600', textTransform: 'uppercase' }}>Action Request Context</th>
                <th style={{ padding: '16px', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: '600', textTransform: 'uppercase' }}>Details / Decision Log</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr
                  key={log.id}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    transition: 'var(--transition-smooth)'
                  }}
                  className="table-row-hover"
                >
                  {/* Timestamp */}
                  <td style={{ padding: '16px', whiteSpace: 'nowrap', fontSize: '13.5px', color: 'var(--text-secondary)' }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  
                  {/* Event Type badge */}
                  <td style={{ padding: '16px' }}>
                    <span className={`badge ${getEventBadgeClass(log.event_type)}`} style={{ fontSize: '11px', padding: '3px 8px' }}>
                      {log.event_type}
                    </span>
                  </td>
                  
                  {/* User */}
                  <td style={{ padding: '16px', fontSize: '14px', fontWeight: '500', color: 'var(--text-primary)' }}>
                    👤 {log.user?.username || `User #${log.user_id}`}
                  </td>
                  
                  {/* Action NL request snippet */}
                  <td style={{ padding: '16px', fontSize: '13.5px', fontStyle: 'italic', color: 'var(--text-secondary)', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {log.action?.natural_language_request ? (
                      <span>"{log.action.natural_language_request}"</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>None</span>
                    )}
                  </td>
                  
                  {/* Event details description */}
                  <td style={{ padding: '16px', fontSize: '13.5px', color: 'var(--text-primary)', lineHeight: '1.4', maxWidth: '300px' }}>
                    {log.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <style>{`
        .table-row-hover:hover {
          background: rgba(255, 255, 255, 0.01) !important;
        }
      `}</style>
    </div>
  );
};

export default AuditLogs;
