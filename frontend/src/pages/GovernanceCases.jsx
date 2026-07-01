import React, { useState, useEffect } from 'react';
import api from '../services/api';

const GovernanceCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [selectedCaseId, setSelectedCaseId] = useState(null);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  // Review form states
  const [comments, setComments] = useState('');
  const [conditions, setConditions] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState(null);

  // Explainability states
  const [explanation, setExplanation] = useState(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [explanationError, setExplanationError] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);

  useEffect(() => {
    fetchCases();
  }, [statusFilter]);

  useEffect(() => {
    if (selectedCaseId) {
      fetchCaseDetail(selectedCaseId);
    } else {
      setSelectedCase(null);
    }
  }, [selectedCaseId]);

  const fetchCases = async () => {
    try {
      setLoading(true);
      setError(null);
      const url = statusFilter === 'ALL' ? '/cases' : `/cases?status_filter=${statusFilter}`;
      const res = await api.get(url);
      setCases(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to retrieve governance cases.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCaseDetail = async (id) => {
    try {
      setLoadingDetail(true);
      setReviewError(null);
      setExplanation(null);
      setShowExplanation(false);
      setExplanationError(null);
      const res = await api.get(`/cases/${id}`);
      setSelectedCase(res.data);
      setComments('');
      setConditions('');
    } catch (err) {
      console.error(err);
      setReviewError('Failed to load detailed case intelligence.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const fetchExplanation = async (id) => {
    try {
      setLoadingExplanation(true);
      setExplanationError(null);
      const res = await api.get(`/cases/${id}/explanation`);
      setExplanation(res.data);
    } catch (err) {
      console.error(err);
      setExplanationError('Failed to load decision explanation report.');
    } finally {
      setLoadingExplanation(false);
    }
  };

  const handleReviewSubmit = async (statusDecision) => {
    if (!selectedCase) return;
    try {
      setSubmittingReview(true);
      setReviewError(null);
      
      const payload = {
        status: statusDecision,
        comments: comments.trim() || null,
        conditions_applied: conditions.trim() || null
      };

      const res = await api.post(`/cases/${selectedCase.id}/review`, payload);
      
      // Update local state
      fetchCases();
      // Reload details to show updated reviewed state
      fetchCaseDetail(selectedCase.id);
    } catch (err) {
      console.error(err);
      setReviewError(err.response?.data?.detail || 'Failed to submit review decision.');
    } finally {
      setSubmittingReview(false);
    }
  };

  const getStatusBadgeClass = (statusVal) => {
    switch (statusVal) {
      case 'APPROVED': return 'badge-success';
      case 'REJECTED': return 'badge-danger';
      case 'MODIFIED': return 'badge-warning';
      case 'PENDING': return 'badge-info';
      default: return 'badge-secondary';
    }
  };

  const getRiskBadgeClass = (score) => {
    if (score <= 30) return 'badge-success';
    if (score <= 60) return 'badge-warning';
    return 'badge-danger';
  };

  return (
    <div className="governance-cases-container fade-in">
      <div className="cases-header" style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', width: 'fit-content' }}>
          Governance Case Manager
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
          Evaluate high-risk AI agent requests, review vector metrics, and submit human decisions.
        </p>
      </div>

      {error && (
        <div className="alert-message error-alert" style={{ padding: '12px 16px', background: 'var(--status-danger-bg)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: 'var(--border-radius-sm)', color: '#ef4444', marginBottom: '20px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Filter Tabs */}
      <div className="filter-tabs" style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        {['PENDING', 'APPROVED', 'REJECTED', 'MODIFIED', 'ALL'].map((filter) => (
          <button
            key={filter}
            onClick={() => { setStatusFilter(filter); setSelectedCaseId(null); }}
            className={`btn-tab ${statusFilter === filter ? 'tab-active' : ''}`}
            style={{
              padding: '8px 16px',
              background: statusFilter === filter ? 'rgba(168, 85, 247, 0.15)' : 'rgba(255, 255, 255, 0.02)',
              border: statusFilter === filter ? '1px solid var(--accent-purple)' : '1px solid var(--glass-border)',
              borderRadius: 'var(--border-radius-sm)',
              color: statusFilter === filter ? 'var(--text-primary)' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: '600',
              transition: 'var(--transition-smooth)'
            }}
          >
            {filter} Cases
          </button>
        ))}
      </div>

      {/* Split Screen Master-Detail Layout */}
      <div className="split-layout" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '24px', alignItems: 'start' }}>
        
        {/* LEFT COLUMN: Cases List */}
        <div className="cases-list-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {loading ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading governance queue...
            </div>
          ) : cases.length === 0 ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              ✨ No cases matching this filter.
            </div>
          ) : (
            cases.map((c) => (
              <div
                key={c.id}
                onClick={() => setSelectedCaseId(c.id)}
                className={`glass-panel case-list-card ${selectedCaseId === c.id ? 'active-case-card' : ''}`}
                style={{
                  padding: '16px',
                  cursor: 'pointer',
                  border: selectedCaseId === c.id ? '1px solid var(--accent-cyan)' : '1px solid var(--glass-border)',
                  background: selectedCaseId === c.id ? 'rgba(6, 182, 212, 0.03)' : 'var(--glass-bg)',
                  transition: 'var(--transition-smooth)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: '600' }}>CASE #{c.id}</span>
                  <span className={`badge ${getStatusBadgeClass(c.status)}`}>{c.status}</span>
                </div>
                
                <h4 style={{ fontSize: '15px', fontWeight: '500', color: 'var(--text-primary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', fontStyle: 'italic' }}>
                  "{c.natural_language_request || (c.action && c.action.natural_language_request)}"
                </h4>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', marginTop: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Domain: <strong style={{ color: 'var(--text-secondary)' }}>{c.domain || (c.action && c.action.domain)}</strong></span>
                  {c.action && (
                    <span className={`badge ${getRiskBadgeClass(c.action.risk_score)}`}>
                      Risk: {c.action.risk_score}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* RIGHT COLUMN: Detail Inspector */}
        <div className="case-detail-panel">
          {loadingDetail ? (
            <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading case breakdown and intelligence...
            </div>
          ) : !selectedCase ? (
            <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-secondary)', minHeight: '350px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '48px' }}>🛡️</span>
              <h3>No Case Selected</h3>
              <p style={{ color: 'var(--text-muted)', maxWidth: '300px', fontSize: '14px' }}>
                Select a case from the list on the left to inspect variables, matched rules, and submit review verdicts.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Core Info Header */}
              <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--accent-purple)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: '600' }}>Case #{selectedCase.id}</h2>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                      Requested by User ID: <strong style={{ color: 'var(--text-secondary)' }}>{selectedCase.action?.requester_id}</strong>
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                    <span className={`badge ${getStatusBadgeClass(selectedCase.status)}`} style={{ fontSize: '14px', padding: '4px 12px' }}>
                      {selectedCase.status}
                    </span>
                    {selectedCase.action && (
                      <span className={`badge ${getRiskBadgeClass(selectedCase.action.risk_score)}`}>
                        Risk Score: {selectedCase.action.risk_score}/100
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.01)', border: '1px solid var(--glass-border)', borderRadius: 'var(--border-radius-sm)', padding: '12px', fontStyle: 'italic', fontSize: '14px', color: 'var(--text-primary)', marginTop: '12px' }}>
                  "{selectedCase.action?.natural_language_request}"
                </div>
              </div>

              {/* Extracted Metadata Card */}
              {selectedCase.action && (
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '14px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>
                    Intent Extraction Data
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', fontSize: '14px' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '12px' }}>Extracted Action</span>
                      <strong style={{ color: 'var(--accent-cyan)' }}>{selectedCase.action.extracted_action || 'N/A'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '12px' }}>Confidence Rating</span>
                      <strong style={{ color: 'var(--text-secondary)' }}>{Math.round((selectedCase.action.confidence || 0) * 100)}%</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '12px' }}>Target Object</span>
                      <strong style={{ color: 'var(--text-secondary)' }}>{selectedCase.action.extracted_object || 'N/A'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '12px' }}>Evaluation Scope</span>
                      <strong style={{ color: 'var(--text-secondary)' }}>{selectedCase.action.extracted_scope || 'N/A'}</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Risk Scoring Breakdown progress bars */}
              {selectedCase.action?.risk_breakdown && (
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '14px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>
                    Risk Scoring Breakdown
                  </h3>
                  
                  <p style={{ fontSize: '13.5px', color: 'var(--text-primary)', fontStyle: 'italic', marginBottom: '16px' }}>
                    💡 {selectedCase.action.risk_breakdown.explanation}
                  </p>

                  <button
                    onClick={() => {
                      if (!showExplanation) {
                        fetchExplanation(selectedCase.id);
                      }
                      setShowExplanation(!showExplanation);
                    }}
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--glass-border)',
                      borderRadius: 'var(--border-radius-sm)',
                      color: 'var(--accent-cyan)',
                      padding: '8px 14px',
                      fontSize: '13px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      marginBottom: '16px',
                      transition: 'all 0.3s ease',
                      width: '100%',
                      justifyContent: 'center'
                    }}
                  >
                    {showExplanation ? '🔍 Hide Detailed Explanation Report' : '🔍 Explain Decision Factors'}
                  </button>

                  {showExplanation && (
                    <div style={{ padding: '14px', background: 'rgba(0,0,0,0.15)', border: '1px solid var(--glass-border)', borderRadius: 'var(--border-radius-sm)', marginBottom: '16px' }}>
                      <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '10px', color: 'var(--accent-cyan)' }}>
                        Explainability Decision Matrix
                      </h4>

                      {loadingExplanation && <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Calculating vector contributions...</div>}
                      {explanationError && <div style={{ fontSize: '13px', color: 'var(--status-danger)' }}>{explanationError}</div>}

                      {explanation && (
                        <div>
                          {/* Risk Equation Breakdown */}
                          <div style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', border: '1px solid var(--glass-border)', borderRadius: 'var(--border-radius-sm)', marginBottom: '16px', fontSize: '13px' }}>
                            <div style={{ color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.05em' }}>Risk Equation</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center', fontWeight: '500', lineHeight: '1.6' }}>
                              {explanation.risk_factors.map((f, i) => (
                                <span key={i} style={{ display: 'inline-flex', alignItems: 'center' }}>
                                  <span style={{ color: 'var(--text-secondary)' }}>{f.name}</span>
                                  <span style={{ color: 'var(--accent-cyan)', marginLeft: '2px' }}>({f.contribution > 0 ? `+${f.contribution}` : f.contribution})</span>
                                  {i < explanation.risk_factors.length - 1 && <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>+</span>}
                                </span>
                              ))}
                              {explanation.adaptive_offset !== 0 && (
                                <>
                                  <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>+</span>
                                  <span style={{ color: 'var(--text-secondary)' }}>Adaptive Offset</span>
                                  <span style={{ color: explanation.adaptive_offset < 0 ? 'var(--status-success)' : 'var(--status-danger)', marginLeft: '2px' }}>
                                    ({explanation.adaptive_offset > 0 ? `+${explanation.adaptive_offset}` : explanation.adaptive_offset})
                                  </span>
                                </>
                              )}
                              <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>=</span>
                              <span style={{ color: 'var(--text-primary)', fontWeight: 'bold', background: 'rgba(255,255,255,0.08)', padding: '2px 6px', borderRadius: '4px' }}>
                                {explanation.final_risk} / 100
                              </span>
                            </div>
                          </div>

                          {/* Risk Factors List */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
                            {explanation.risk_factors.map((f, i) => (
                              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: 'var(--border-radius-sm)', fontSize: '13px' }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                  <strong style={{ color: 'var(--text-secondary)' }}>{f.name}</strong>
                                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{f.description}</span>
                                </div>
                                <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                                  <span style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>+{f.contribution} pts</span>
                                  <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Score: {f.score}% (Weight: {f.weight}%)</span>
                                </div>
                              </div>
                            ))}
                            {explanation.adaptive_offset !== 0 && (
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px', background: explanation.adaptive_offset < 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: 'var(--border-radius-sm)', fontSize: '13px' }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                  <strong style={{ color: explanation.adaptive_offset < 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>Adaptive Learning Adjustment</strong>
                                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                                    {explanation.adaptive_offset < 0 ? 'Decreased risk due to repeated approvals' : 'Increased risk due to repeated rejections'}
                                  </span>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                  <span style={{ color: explanation.adaptive_offset < 0 ? 'var(--status-success)' : 'var(--status-danger)', fontWeight: '600' }}>
                                    {explanation.adaptive_offset > 0 ? `+${explanation.adaptive_offset}` : explanation.adaptive_offset} pts
                                  </span>
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Matched Policies Contribution Breakdown */}
                          {explanation.matched_policies.length > 0 && (
                            <div style={{ marginTop: '14px' }}>
                              <h4 style={{ fontSize: '12px', fontWeight: '600', color: 'var(--status-warning)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>
                                Policy Contribution Breakdown
                              </h4>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {explanation.matched_policies.map((p, idx) => (
                                  <div key={idx} style={{ padding: '10px', background: 'rgba(245, 158, 11, 0.02)', border: '1px solid rgba(245, 158, 11, 0.1)', borderRadius: 'var(--border-radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12.5px' }}>
                                    <div>
                                      <strong style={{ color: 'var(--text-secondary)' }}>{p.name}</strong>
                                      <span className={`badge ${p.severity === 'CRITICAL' ? 'badge-danger' : p.severity === 'HIGH' ? 'badge-warning' : p.severity === 'MEDIUM' ? 'badge-info' : 'badge-secondary'}`} style={{ marginLeft: '8px', fontSize: '10px', padding: '1px 6px' }}>
                                        {p.severity}
                                      </span>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                      <span style={{ color: 'var(--status-warning)', fontWeight: '600' }}>+{p.contribution} pts</span>
                                      <span style={{ color: 'var(--text-muted)', fontSize: '10px', display: 'block' }}>Boost: +{p.boost}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
                    {[
                      { label: "Domain Risk", val: selectedCase.action.risk_breakdown.domain_factor },
                      { label: "Reversibility Impact", val: selectedCase.action.risk_breakdown.reversibility_factor },
                      { label: "Scope Exposure", val: selectedCase.action.risk_breakdown.scope_factor },
                      { label: "Policy Violations", val: selectedCase.action.risk_breakdown.policy_factor },
                      { label: "AI Conf Mismatch", val: selectedCase.action.risk_breakdown.confidence_factor },
                      { label: "History Rejections", val: selectedCase.action.risk_breakdown.history_factor },
                      { label: "Safety Compliance", val: selectedCase.action.risk_breakdown.safety_factor || 0 }
                    ].map((vector, i) => (
                      <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)' }}>
                          <span>{vector.label}</span>
                          <span style={{ fontWeight: '600', color: 'var(--text-secondary)' }}>{Math.round(vector.val * 100)}%</span>
                        </div>
                        <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${vector.val * 100}%`,
                            height: '100%',
                            background: vector.val <= 0.3 ? 'var(--status-success)' :
                                       vector.val <= 0.6 ? 'var(--status-warning)' : 'var(--status-danger)',
                            borderRadius: '3px'
                          }} />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Detailed Safety Compliance Metrics */}
                  {selectedCase.action.risk_breakdown.safety_factor !== undefined && (
                    <div style={{ marginTop: '18px', paddingTop: '18px', borderTop: '1px solid var(--glass-border)' }}>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--accent-cyan)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        🛡️ NIST Trust & Safety Compliance Metrics
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                        {[
                          { label: "Negation Risk", val: selectedCase.action.risk_breakdown.negation || 0 },
                          { label: "Harmful Bias", val: selectedCase.action.risk_breakdown.harmful_biasness || 0 },
                          { label: "Confabulation", val: selectedCase.action.risk_breakdown.confabulation || 0 },
                          { label: "Integrity Violation", val: Math.max(0, 1.0 - (selectedCase.action.risk_breakdown.integrity !== undefined ? selectedCase.action.risk_breakdown.integrity : 1)) },
                          { label: "Abusive Content", val: selectedCase.action.risk_breakdown.abusive || 0 },
                          { label: "Privacy Exposure", val: Math.max(0, 1.0 - (selectedCase.action.risk_breakdown.privacy_enhanced !== undefined ? selectedCase.action.risk_breakdown.privacy_enhanced : 1)) },
                          { label: "Dangerous Intent", val: selectedCase.action.risk_breakdown.dangerous || 0 },
                          { label: "Violent Content", val: selectedCase.action.risk_breakdown.violent || 0 },
                          { label: "Environmental Footprint", val: selectedCase.action.risk_breakdown.environmental_impacts || 0 }
                        ].map((sub, idx) => (
                          <div key={idx} style={{ padding: '8px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '4px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                              <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }} title={sub.label}>{sub.label}</span>
                              <span style={{ fontWeight: '600', color: sub.val > 0.5 ? 'var(--status-danger)' : sub.val > 0.2 ? 'var(--status-warning)' : 'var(--text-secondary)' }}>
                                {Math.round(sub.val * 100)}%
                              </span>
                            </div>
                            <div style={{ height: '4px', background: 'rgba(255,255,255,0.03)', borderRadius: '2px', overflow: 'hidden' }}>
                              <div style={{
                                width: `${sub.val * 100}%`,
                                height: '100%',
                                background: sub.val <= 0.2 ? 'var(--status-success)' :
                                           sub.val <= 0.5 ? 'var(--status-warning)' : 'var(--status-danger)',
                                borderRadius: '2px'
                              }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Matched Policies Exception logs */}
              {selectedCase.action?.matched_policies && selectedCase.action.matched_policies.length > 0 && (
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '14px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px', color: 'var(--status-warning)' }}>
                    Triggered Policy Exceptions
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {selectedCase.action.matched_policies.map((p, idx) => (
                      <div key={idx} style={{
                        padding: '12px',
                        background: 'rgba(245, 158, 11, 0.04)',
                        border: '1px solid rgba(245, 158, 11, 0.15)',
                        borderRadius: 'var(--border-radius-sm)',
                        fontSize: '13.5px'
                      }}>
                        <strong style={{ color: 'var(--status-warning)', display: 'block', marginBottom: '4px' }}>🛡️ {p}</strong>
                        <span style={{ color: 'var(--text-secondary)' }}>{selectedCase.action.violations?.[idx]}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Questionnaire Logs */}
              {selectedCase.action?.clarification_questions && selectedCase.action.clarification_questions.length > 0 && (
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '14px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>
                    Clarification logs
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {selectedCase.action.clarification_questions.map((q) => (
                      <div key={q.id} style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '13.5px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Q: {q.question_text}</span>
                        <strong style={{ color: 'var(--accent-cyan)' }}>A: {q.answer?.answer_text || 'No answer recorded'}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Review Input Box (Active Decision Engine Action) */}
              {selectedCase.status === 'PENDING' ? (
                <div className="glass-panel" style={{ padding: '20px', borderTop: '4px solid var(--accent-cyan)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '14px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>
                    Review Decision Console
                  </h3>
                  
                  {reviewError && (
                    <div style={{ padding: '10px', background: 'var(--status-danger-bg)', color: '#ef4444', borderRadius: 'var(--border-radius-sm)', fontSize: '13px', marginBottom: '14px' }}>
                      ⚠️ {reviewError}
                    </div>
                  )}

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: '500' }}>
                        Reviewer Comments & Justification
                      </label>
                      <textarea
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        placeholder="Provide reason for approval/rejection decision..."
                        style={{
                          width: '100%',
                          minHeight: '80px',
                          background: 'rgba(0,0,0,0.2)',
                          border: '1px solid var(--glass-border)',
                          borderRadius: 'var(--border-radius-sm)',
                          padding: '10px',
                          color: '#fff',
                          fontFamily: 'inherit',
                          fontSize: '14px',
                          resize: 'vertical'
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: '500' }}>
                        Conditions Applied (e.g. scheduling limits, rollbacks)
                      </label>
                      <textarea
                        value={conditions}
                        onChange={(e) => setConditions(e.target.value)}
                        placeholder="Specify rules or boundary constraints if approving..."
                        style={{
                          width: '100%',
                          minHeight: '60px',
                          background: 'rgba(0,0,0,0.2)',
                          border: '1px solid var(--glass-border)',
                          borderRadius: 'var(--border-radius-sm)',
                          padding: '10px',
                          color: '#fff',
                          fontFamily: 'inherit',
                          fontSize: '14px',
                          resize: 'vertical'
                        }}
                      />
                    </div>

                    <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                      <button
                        onClick={() => handleReviewSubmit('APPROVED')}
                        disabled={submittingReview}
                        className="btn-success"
                        style={{
                          flex: 1,
                          padding: '12px',
                          background: 'var(--status-success)',
                          border: 'none',
                          borderRadius: 'var(--border-radius-sm)',
                          color: '#fff',
                          fontWeight: '600',
                          cursor: 'pointer',
                          transition: 'var(--transition-smooth)'
                        }}
                      >
                        {submittingReview ? 'Submitting...' : '✅ Approve Case'}
                      </button>

                      <button
                        onClick={() => handleReviewSubmit('REJECTED')}
                        disabled={submittingReview}
                        className="btn-danger"
                        style={{
                          flex: 1,
                          padding: '12px',
                          background: 'var(--status-danger)',
                          border: 'none',
                          borderRadius: 'var(--border-radius-sm)',
                          color: '#fff',
                          fontWeight: '600',
                          cursor: 'pointer',
                          transition: 'var(--transition-smooth)'
                        }}
                      >
                        {submittingReview ? 'Submitting...' : '❌ Reject Case'}
                      </button>

                      <button
                        onClick={() => handleReviewSubmit('MODIFIED')}
                        disabled={submittingReview}
                        className="btn-warning"
                        style={{
                          flex: 1,
                          padding: '12px',
                          background: 'var(--status-warning)',
                          border: 'none',
                          borderRadius: 'var(--border-radius-sm)',
                          color: '#fff',
                          fontWeight: '600',
                          cursor: 'pointer',
                          transition: 'var(--transition-smooth)'
                        }}
                      >
                        {submittingReview ? 'Submitting...' : '⚠️ Modify Rules'}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass-panel" style={{ padding: '20px', borderLeft: '4px solid var(--text-muted)' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '10px' }}>
                    Historical Review Record
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13.5px' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Reviewer User ID:</span>{' '}
                      <strong>{selectedCase.reviewer_id || 'System'}</strong>
                    </div>
                    {selectedCase.comments && (
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Reviewer Comments:</span>
                        <p style={{ marginTop: '4px', padding: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--glass-border)', borderRadius: 'var(--border-radius-sm)' }}>
                          {selectedCase.comments}
                        </p>
                      </div>
                    )}
                    {selectedCase.conditions_applied && (
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Conditions Enforced:</span>
                        <p style={{ marginTop: '4px', padding: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--glass-border)', borderRadius: 'var(--border-radius-sm)', color: 'var(--accent-cyan)' }}>
                          {selectedCase.conditions_applied}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default GovernanceCases;
