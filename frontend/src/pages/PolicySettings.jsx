import React, { useEffect, useState, useRef } from 'react';
import api from '../services/api';

const PolicySettings = () => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filtering & Search
  const [selectedTab, setSelectedTab] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Form fields
  const [editingId, setEditingId] = useState(null);
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('ALL');
  const [actionType, setActionType] = useState('ALL');
  const [severity, setSeverity] = useState('MEDIUM');
  const [description, setDescription] = useState('');
  
  // Rule definition fields
  const [conditionType, setConditionType] = useState('domain_specific');
  const [thresholdValue, setThresholdValue] = useState(0);
  const [regulation, setRegulation] = useState('');

  // File Upload State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const fileInputRef = useRef(null);

  const fetchPolicies = async () => {
    try {
      const res = await api.get('/policies');
      setPolicies(res.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load policies:', err);
      setError('Could not retrieve policies from database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const resetForm = () => {
    setEditingId(null);
    setName('');
    setDomain('ALL');
    setActionType('ALL');
    setSeverity('MEDIUM');
    setDescription('');
    setConditionType('domain_specific');
    setThresholdValue(0);
    setRegulation('');
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const payload = {
      name,
      domain,
      description,
      action_type: actionType,
      severity,
      rule_definition: {
        category: 'Compliance',
        condition_type: conditionType,
        operator: conditionType.includes('threshold') ? '>' : '',
        threshold_value: parseInt(thresholdValue) || 0,
        regulation
      },
      is_active: true
    };

    try {
      if (editingId) {
        await api.put(`/policies/${editingId}`, payload);
      } else {
        await api.post('/policies', payload);
      }
      resetForm();
      fetchPolicies();
    } catch (err) {
      console.error('Failed to save policy:', err);
      alert(err.response?.data?.detail || 'Failed to save policy.');
    }
  };

  const handleEdit = (p) => {
    setEditingId(p.id);
    setName(p.name);
    setDomain(p.domain);
    setActionType(p.action_type);
    setSeverity(p.severity);
    setDescription(p.description || '');
    setConditionType(p.rule_definition?.condition_type || 'domain_specific');
    setThresholdValue(p.rule_definition?.threshold_value || 0);
    setRegulation(p.rule_definition?.regulation || '');
    // Scroll form into view on mobile
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this policy?')) return;
    try {
      await api.delete(`/policies/${id}`);
      fetchPolicies();
    } catch (err) {
      console.error('Failed to delete policy:', err);
    }
  };

  const handleToggleActive = async (p) => {
    const updated = {
      ...p,
      is_active: !p.is_active,
      rule_definition: p.rule_definition || { category: 'Compliance', condition_type: 'domain_specific', operator: '', threshold_value: 0, regulation: '' }
    };
    try {
      await api.put(`/policies/${p.id}`, updated);
      fetchPolicies();
    } catch (err) {
      console.error('Failed to toggle policy status:', err);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadStatus(null);
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      await api.post('/policies/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus({ success: true, message: 'Policy file uploaded and parsed successfully!' });
      setUploadFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchPolicies();
    } catch (err) {
      console.error('File upload failed:', err);
      setUploadStatus({ success: false, message: err.response?.data?.detail || 'Failed to parse policy text file.' });
    } finally {
      setUploading(false);
    }
  };

  // Filter policies based on Search Input & Active Tab
  const filteredPolicies = policies.filter(p => {
    const matchesTab = selectedTab === 'ALL' || p.domain.toUpperCase() === selectedTab.toUpperCase();
    const matchesSearch = 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      p.domain.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  return (
    <div className="policy-settings-container fade-in">
      <div className="policy-header-row">
        <div>
          <h1 className="page-title">🛡️ Policy & Guardrail Registry</h1>
          <p className="page-desc">Define corporate governance thresholds, target environment checks, and upload text compliance rules.</p>
        </div>
      </div>

      <div className="policy-grid">
        {/* Form and File Upload Column */}
        <div className="form-column">
          {/* Manual Policy Form */}
          <div className="glass-panel form-panel">
            <h2 className="section-title">{editingId ? '✏️ Edit Policy Rule' : '➕ Register New Policy'}</h2>
            <form onSubmit={handleSave} className="manual-policy-form">
              <div className="form-group">
                <label>Policy Name</label>
                <input 
                  type="text" 
                  value={name} 
                  onChange={(e) => setName(e.target.value)} 
                  required 
                  placeholder="e.g. Bulk Deletion Guardrail"
                  className="premium-input"
                />
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label>Domain</label>
                  <select value={domain} onChange={(e) => setDomain(e.target.value)} className="premium-select">
                    <option value="ALL">ALL Domains</option>
                    <option value="Finance">Finance</option>
                    <option value="Healthcare">Healthcare</option>
                    <option value="HR">HR</option>
                    <option value="Legal">Legal</option>
                    <option value="Manufacturing">Manufacturing</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Action Type</label>
                  <select value={actionType} onChange={(e) => setActionType(e.target.value)} className="premium-select">
                    <option value="ALL">ALL Actions</option>
                    <option value="DELETE">DELETE</option>
                    <option value="TRANSFER">TRANSFER</option>
                    <option value="UPDATE">UPDATE</option>
                    <option value="CREATE">CREATE</option>
                  </select>
                </div>
              </div>

              <div className="form-row-2">
                <div className="form-group">
                  <label>Severity</label>
                  <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="premium-select">
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Condition Checker</label>
                  <select value={conditionType} onChange={(e) => setConditionType(e.target.value)} className="premium-select">
                    <option value="domain_specific">Domain Action Match (Always triggers)</option>
                    <option value="threshold">Financial Amount Threshold</option>
                    <option value="bulk_threshold">Record Volume Threshold</option>
                    <option value="production_check">Production Environment Safeguard</option>
                  </select>
                </div>
              </div>

              {conditionType.includes('threshold') && (
                <div className="form-group">
                  <label>Threshold Value</label>
                  <input 
                    type="number" 
                    value={thresholdValue} 
                    onChange={(e) => setThresholdValue(e.target.value)} 
                    required 
                    placeholder="Enter limit value"
                    className="premium-input"
                  />
                </div>
              )}

              <div className="form-group">
                <label>Compliance Regulation Reference (Optional)</label>
                <input 
                  type="text" 
                  value={regulation} 
                  onChange={(e) => setRegulation(e.target.value)} 
                  placeholder="e.g. GDPR Art 25, HIPAA, PCI DSS"
                  className="premium-input"
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea 
                  value={description} 
                  onChange={(e) => setDescription(e.target.value)} 
                  rows="3" 
                  placeholder="Describe compliance rules and constraints"
                  className="premium-textarea"
                />
              </div>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary">
                  {editingId ? 'Save Update ✓' : 'Register Policy +'}
                </button>
                {editingId && (
                  <button type="button" onClick={resetForm} className="btn btn-secondary">
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* Text File Upload Section */}
          <div className="glass-panel upload-panel">
            <h2 className="section-title">📤 Upload Policy Document</h2>
            <p className="upload-desc">Upload a `.txt` policy document. Unstructured files will be fully imported as single guidelines to ensure clarity and decision-making accuracy.</p>
            <form onSubmit={handleFileUpload} className="upload-policy-form">
              <div 
                className="dropzone-container"
                onClick={() => fileInputRef.current && fileInputRef.current.click()}
              >
                <div className="dropzone-icon">📄</div>
                <div className="dropzone-text">
                  {uploadFile ? (
                    <span className="file-selected">{uploadFile.name}</span>
                  ) : (
                    <span>Click to choose or drag a policy <strong>.txt</strong> file</span>
                  )}
                </div>
                <input 
                  type="file" 
                  accept=".txt" 
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  ref={fileInputRef}
                  required
                  style={{ display: 'none' }}
                />
              </div>
              <button 
                type="submit" 
                className="btn btn-secondary upload-btn" 
                disabled={uploading || !uploadFile}
              >
                {uploading ? 'Parsing...' : 'Upload Text Rule'}
              </button>
            </form>
            
            {uploadStatus && (
              <div className={`upload-status-message ${uploadStatus.success ? 'success' : 'error'}`}>
                {uploadStatus.message}
              </div>
            )}
          </div>
        </div>

        {/* Policies List Column */}
        <div className="list-column">
          {/* Tabs and Search Filters */}
          <div className="filters-container glass-panel">
            <div className="search-bar-wrapper">
              <span className="search-icon">🔍</span>
              <input 
                type="text" 
                placeholder="Search policies by name, domain, description..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>
            
            <div className="tabs-row">
              {['ALL', 'FINANCE', 'HEALTHCARE', 'HR', 'LEGAL', 'MANUFACTURING'].map((tab) => (
                <button 
                  key={tab} 
                  className={`tab-btn ${selectedTab === tab ? 'active' : ''}`}
                  onClick={() => setSelectedTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          <div className="glass-panel list-panel">
            <h2 className="section-title">Active Policy Catalog ({filteredPolicies.length})</h2>
            
            {loading ? (
              <div className="loading-state">Loading policy rules...</div>
            ) : error ? (
              <div className="error-state">{error}</div>
            ) : filteredPolicies.length === 0 ? (
              <div className="empty-state">No policy guidelines match your criteria.</div>
            ) : (
              <div className="policy-list">
                {filteredPolicies.map((p) => (
                  <div key={p.id} className={`policy-item-card ${p.is_active ? 'active' : 'inactive'}`}>
                    <div className="policy-item-top">
                      <div>
                        <div className="policy-item-title-row">
                          <strong className="policy-title-txt">{p.name}</strong>
                          <span className={`badge severity-badge ${p.severity.toLowerCase()}`}>
                            {p.severity}
                          </span>
                        </div>
                        <div className="policy-meta-badges">
                          <span className="meta-badge">Domain: {p.domain}</span>
                          <span className="meta-badge">Action: {p.action_type}</span>
                          {p.rule_definition?.regulation && (
                            <span className="meta-badge regulation">{p.rule_definition.regulation}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="policy-item-controls">
                        <label className="toggle-switch" title={p.is_active ? 'Deactivate policy' : 'Activate policy'}>
                          <input 
                            type="checkbox" 
                            checked={p.is_active} 
                            onChange={() => handleToggleActive(p)} 
                          />
                          <span className="slider"></span>
                        </label>
                      </div>
                    </div>

                    <p className="policy-description-txt">{p.description}</p>
                    
                    <div className="policy-item-footer">
                      <span className="condition-indicator">
                        Trigger: <code>{p.rule_definition?.condition_type}</code>
                        {p.rule_definition?.threshold_value > 0 && ` (${p.rule_definition.operator} ${p.rule_definition.threshold_value})`}
                      </span>
                      
                      <div className="policy-footer-actions">
                        <button onClick={() => handleEdit(p)} className="btn-edit" title="Edit policy">
                          ✏️ Edit
                        </button>
                        <button onClick={() => handleDelete(p.id)} className="btn-delete" title="Delete policy">
                          🗑️ Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .policy-settings-container {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .policy-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          text-align: left;
        }

        .page-title {
          font-size: 26px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 6px;
          letter-spacing: -0.02em;
        }

        .page-desc {
          font-size: 14.5px;
          color: var(--text-secondary);
          margin: 0;
        }

        .policy-grid {
          display: grid;
          grid-template-columns: 430px 1fr;
          gap: 24px;
          align-items: start;
        }

        .form-column {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .form-panel, .upload-panel, .list-panel, .filters-container {
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 18px;
          align-items: flex-start;
          text-align: left;
          border: 1px solid var(--glass-border);
          box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        }

        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .manual-policy-form {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
          width: 100%;
        }

        .form-group label {
          font-size: 12.5px;
          font-weight: 600;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.02em;
        }

        .premium-input, .premium-select, .premium-textarea {
          background: rgba(255, 255, 255, 0.03) !important;
          border: 1px solid var(--glass-border) !important;
          border-radius: 6px !important;
          color: var(--text-primary) !important;
          padding: 10px 14px !important;
          font-size: 14px !important;
          outline: none !important;
          transition: all 0.2s ease-in-out !important;
          width: 100% !important;
        }

        .premium-input:focus, .premium-select:focus, .premium-textarea:focus {
          border-color: var(--accent-cyan) !important;
          box-shadow: 0 0 10px rgba(6, 182, 212, 0.15) !important;
          background: rgba(255, 255, 255, 0.06) !important;
        }

        .form-row-2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
          width: 100%;
        }

        .form-actions {
          display: flex;
          gap: 12px;
          margin-top: 10px;
          width: 100%;
        }

        .btn {
          padding: 10px 20px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
          text-align: center;
        }

        .btn-primary {
          background: linear-gradient(135deg, var(--accent-cyan) 0%, #0891b2 100%);
          color: #0b0f19;
          box-shadow: 0 4px 15px rgba(6, 182, 212, 0.25);
        }

        .btn-primary:hover {
          transform: translateY(-1px);
          box-shadow: 0 6px 20px rgba(6, 182, 212, 0.35);
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid var(--glass-border);
          color: var(--text-primary);
        }

        .btn-secondary:hover {
          background: rgba(255, 255, 255, 0.15);
        }

        /* Upload File styles */
        .upload-desc {
          font-size: 13.5px;
          color: var(--text-secondary);
          line-height: 1.5;
          margin: 0;
        }

        .upload-policy-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
          width: 100%;
        }

        .dropzone-container {
          background: rgba(0, 0, 0, 0.2);
          border: 2px dashed var(--glass-border);
          border-radius: 8px;
          padding: 24px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .dropzone-container:hover {
          border-color: var(--accent-cyan);
          background: rgba(6, 182, 212, 0.02);
        }

        .dropzone-icon {
          font-size: 28px;
        }

        .dropzone-text {
          font-size: 13px;
          color: var(--text-secondary);
        }

        .dropzone-text strong {
          color: var(--accent-cyan);
        }

        .file-selected {
          color: var(--status-success);
          font-weight: 600;
        }

        .upload-btn {
          width: 100%;
          padding: 10px 0;
          font-size: 14px;
        }

        .upload-status-message {
          font-size: 13px;
          padding: 10px 14px;
          border-radius: 6px;
          width: 100%;
          line-height: 1.4;
        }

        .upload-status-message.success {
          background: rgba(34, 197, 94, 0.08);
          border: 1px solid rgba(34, 197, 94, 0.2);
          color: var(--status-success);
        }

        .upload-status-message.error {
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: var(--status-danger);
        }

        /* Search and Tabs filters */
        .filters-container {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .search-bar-wrapper {
          display: flex;
          align-items: center;
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--glass-border);
          border-radius: 6px;
          padding: 6px 14px;
          width: 100%;
        }

        .search-icon {
          margin-right: 10px;
          color: var(--text-muted);
        }

        .search-input {
          background: none;
          border: none;
          color: var(--text-primary);
          outline: none;
          font-size: 14.5px;
          width: 100%;
          padding: 6px 0;
        }

        .tabs-row {
          display: flex;
          gap: 8px;
          width: 100%;
          overflow-x: auto;
          padding-bottom: 4px;
        }

        .tab-btn {
          background: none;
          border: 1px solid var(--glass-border);
          color: var(--text-secondary);
          padding: 6px 14px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
        }

        .tab-btn:hover {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-primary);
        }

        .tab-btn.active {
          background: var(--accent-cyan);
          color: #0b0f19;
          border-color: var(--accent-cyan);
        }

        /* List Column */
        .list-panel {
          width: 100%;
        }

        .policy-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
          width: 100%;
        }

        .policy-item-card {
          padding: 20px;
          border: 1px solid var(--glass-border);
          border-radius: 8px;
          background: rgba(255, 255, 255, 0.01);
          display: flex;
          flex-direction: column;
          gap: 12px;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .policy-item-card.active {
          border-left: 4px solid var(--accent-cyan);
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }

        .policy-item-card.active:hover {
          transform: translateY(-2px);
          border-color: var(--accent-cyan);
          box-shadow: 0 6px 24px rgba(6, 182, 212, 0.1);
        }

        .policy-item-card.inactive {
          opacity: 0.45;
          border-style: dashed;
        }

        .policy-item-top {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          width: 100%;
        }

        .policy-item-title-row {
          display: flex;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }

        .policy-title-txt {
          font-size: 16px;
          color: var(--text-primary);
          font-weight: 600;
          letter-spacing: -0.01em;
        }

        .severity-badge {
          font-size: 10px;
          padding: 3px 8px;
          font-weight: 700;
          border-radius: 4px;
          letter-spacing: 0.05em;
        }

        .severity-badge.low { background: rgba(34, 197, 94, 0.1); color: var(--status-success); border: 1px solid rgba(34, 197, 94, 0.2); }
        .severity-badge.medium { background: rgba(234, 179, 8, 0.1); color: var(--status-warning); border: 1px solid rgba(234, 179, 8, 0.2); }
        .severity-badge.high { background: rgba(249, 115, 22, 0.1); color: var(--status-warning); border: 1px solid rgba(249, 115, 22, 0.2); }
        .severity-badge.critical { background: rgba(239, 68, 68, 0.1); color: var(--status-danger); border: 1px solid rgba(239, 68, 68, 0.2); }

        .policy-meta-badges {
          display: flex;
          gap: 8px;
          margin-top: 8px;
          flex-wrap: wrap;
        }

        .meta-badge {
          font-size: 11.5px;
          padding: 3px 10px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--glass-border);
          color: var(--text-secondary);
          border-radius: 12px;
        }

        .meta-badge.regulation {
          background: rgba(6, 182, 212, 0.05);
          color: var(--accent-cyan);
          border-color: rgba(6, 182, 212, 0.2);
        }

        .policy-description-txt {
          margin: 0;
          font-size: 14px;
          color: var(--text-secondary);
          line-height: 1.6;
          white-space: pre-wrap;
        }

        .policy-item-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-top: 1px solid rgba(255, 255, 255, 0.05);
          padding-top: 12px;
          margin-top: 4px;
          width: 100%;
        }

        .condition-indicator {
          font-size: 12.5px;
          color: var(--text-muted);
        }

        .condition-indicator code {
          background: rgba(0, 0, 0, 0.35);
          padding: 3px 8px;
          border-radius: 4px;
          color: var(--text-secondary);
          font-size: 11.5px;
        }

        .policy-footer-actions {
          display: flex;
          gap: 16px;
        }

        .btn-edit, .btn-delete {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          padding: 0;
          transition: all 0.2s ease;
        }

        .btn-edit { color: var(--accent-cyan); }
        .btn-delete { color: var(--status-danger); }

        .btn-edit:hover, .btn-delete:hover {
          opacity: 0.75;
          transform: scale(1.02);
        }

        /* Toggle switch */
        .toggle-switch {
          position: relative;
          display: inline-block;
          width: 38px;
          height: 22px;
        }

        .toggle-switch input {
          opacity: 0;
          width: 0;
          height: 0;
        }

        .slider {
          position: absolute;
          cursor: pointer;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(255, 255, 255, 0.08);
          transition: .3s;
          border-radius: 24px;
          border: 1px solid var(--glass-border);
        }

        .slider:before {
          position: absolute;
          content: "";
          height: 14px;
          width: 14px;
          left: 3px;
          bottom: 3px;
          background-color: #cbd5e1;
          transition: .3s;
          border-radius: 50%;
        }

        input:checked + .slider {
          background-color: var(--accent-cyan);
        }

        input:checked + .slider:before {
          background-color: #0b0f19;
          transform: translateX(16px);
        }

        .loading-state, .error-state, .empty-state {
          padding: 60px 40px;
          text-align: center;
          color: var(--text-muted);
          font-size: 14.5px;
          width: 100%;
        }
      `}</style>
    </div>
  );
};

export default PolicySettings;
