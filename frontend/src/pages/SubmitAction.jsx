import React, { useState } from 'react';
import api from '../services/api';

const SubmitAction = () => {
  const [domain, setDomain] = useState('Finance');
  const [request, setRequest] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Clarification Questionnaire States
  const [clarificationQuestions, setClarificationQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [submittingAnswers, setSubmittingAnswers] = useState(false);

  const fetchClarifications = async (actionId) => {
    try {
      const res = await api.get(`/actions/${actionId}/clarifications`);
      setClarificationQuestions(res.data);
      
      // Initialize answers structure
      const initialAnswers = {};
      res.data.forEach((q) => {
        initialAnswers[q.id] = '';
      });
      setAnswers(initialAnswers);
    } catch (err) {
      console.error("Failed to load clarifications:", err);
      setError("Failed to retrieve clarification questions from the server.");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setClarificationQuestions([]);
    setAnswers({});

    if (!request.trim()) {
      setError("Please enter your action request details");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/actions/evaluate', {
        domain,
        natural_language_request: request
      });
      
      setResult(response.data);
      setRequest(''); // Clear request text box
      
      // If the action is awaiting clarifications, trigger loading questions
      if (response.data.status === 'AWAITING_CLARIFICATION') {
        await fetchClarifications(response.data.id);
      }
    } catch (err) {
      console.error("Action evaluation failed:", err);
      setError(err.response?.data?.detail || "Failed to submit request to Governance Engine");
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validate that all fields have answers
    const unanswered = clarificationQuestions.filter(q => !answers[q.id]?.trim());
    if (unanswered.length > 0) {
      setError("Please answer all clarification questions before submitting.");
      return;
    }

    setSubmittingAnswers(true);
    try {
      // Submit each answer to the backend questions endpoint
      const submitPromises = clarificationQuestions.map(q => 
        api.post(`/actions/questions/${q.id}/answer`, {
          answer_text: answers[q.id]
        })
      );
      await Promise.all(submitPromises);

      // Re-fetch action details to refresh results after solving questionnaire
      const res = await api.get(`/actions/${result.id}`);
      setResult(res.data);
      setClarificationQuestions([]);
      setAnswers({});
    } catch (err) {
      console.error("Failed to submit clarification answers:", err);
      setError(err.response?.data?.detail || "Error committing clarification answers");
    } finally {
      setSubmittingAnswers(false);
    }
  };

  return (
    <div className="submit-action-container fade-in">
      <div className="glass-panel form-section">
        <h2>Submit Natural Language Action</h2>
        <p className="subtitle">Enter a business task. The Governance Engine will evaluate risk and autonomy constraints.</p>
        
        {error && (
          <div className="alert alert-danger">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="action-form">
          <div className="input-group">
            <label className="input-label" htmlFor="domain">Business Domain</label>
            <select
              id="domain"
              className="select-field"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              disabled={loading || submittingAnswers}
            >
              <option value="Finance">Finance</option>
              <option value="Healthcare">Healthcare</option>
              <option value="HR">HR (Human Resources)</option>
              <option value="Legal">Legal</option>
              <option value="Manufacturing">Manufacturing</option>
            </select>
          </div>

          <div className="input-group">
            <label className="input-label" htmlFor="request">Natural Language Request</label>
            <textarea
              id="request"
              className="input-field textarea-field"
              placeholder="e.g., Transfer ₹50,000 to John Doe or Delete patient record ID 98765"
              rows={4}
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              disabled={loading || submittingAnswers}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading || submittingAnswers}>
            {loading ? 'Evaluating Action...' : 'Submit to Governance Engine ⚡'}
          </button>
        </form>
      </div>

      {/* Result & Clarification Section */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', width: '100%' }}>
          {/* Result Summary Card */}
          <div className="glass-panel result-section fade-in">
            <div className="result-header">
              <h3>Evaluation Result</h3>
              <span className="badge badge-info">Action ID: {result.id}</span>
            </div>
            
            <div className="result-grid">
              <div className="result-item">
                <span className="result-label">Domain</span>
                <span className="result-val">{result.domain}</span>
              </div>
              
              <div className="result-item">
                <span className="result-label">Autonomy Level</span>
                <span className={`badge ${
                  result.autonomy_level === 'AUTOMATIC' ? 'badge-success' :
                  result.autonomy_level === 'USER_CONFIRMATION' ? 'badge-warning' : 'badge-danger'
                }`}>
                  {result.autonomy_level}
                </span>
              </div>

              <div className="result-item">
                <span className="result-label">Risk Score</span>
                <span className="result-val risk-value" style={{
                  color: result.risk_score <= 30 ? 'var(--status-success)' :
                         result.risk_score <= 60 ? 'var(--status-warning)' : 'var(--status-danger)'
                }}>
                  {result.risk_score} / 100
                </span>
              </div>

              <div className="result-item">
                <span className="result-label">Submission Status</span>
                <span className={`badge ${
                  result.status === 'PENDING' ? 'badge-info' :
                  result.status === 'AWAITING_CLARIFICATION' ? 'badge-warning' : 'badge-success'
                }`}>{result.status}</span>
              </div>
            </div>

            <div className="result-details">
              <div className="result-details-title">Natural Language Request:</div>
              <p className="request-quote">"{result.natural_language_request}"</p>
              {result.extracted_scope && result.extracted_scope.includes('| Context:') && (
                <div style={{ marginTop: '12px', borderTop: '1px solid var(--glass-border)', paddingTop: '8px' }}>
                  <div className="result-details-title">Provided Context:</div>
                  <p style={{ fontSize: '14px', color: 'var(--accent-cyan)' }}>
                    {result.extracted_scope.split('| Context:')[1].trim()}
                  </p>
                </div>
              )}
            </div>
            
            {result.risk_breakdown && (
              <div className="risk-breakdown-box fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="result-details-title" style={{ fontWeight: '600' }}>Risk Vectors Analysis:</div>
                <div style={{ padding: '14px', background: 'rgba(15, 23, 42, 0.3)', border: '1px solid var(--glass-border)', borderRadius: 'var(--border-radius-sm)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <p style={{ fontSize: '13.5px', color: 'var(--text-primary)', fontStyle: 'italic', margin: '0 0 8px 0' }}>
                    💡 {result.risk_breakdown.explanation}
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                    {[
                      { label: "Domain Risk", val: result.risk_breakdown.domain_factor },
                      { label: "Reversibility Impact", val: result.risk_breakdown.reversibility_factor },
                      { label: "Scope Exposure", val: result.risk_breakdown.scope_factor },
                      { label: "Policy Violations", val: result.risk_breakdown.policy_factor },
                      { label: "AI Conf. Mismatch", val: result.risk_breakdown.confidence_factor },
                      { label: "History Rejections", val: result.risk_breakdown.history_factor },
                      { label: "Safety Compliance", val: result.risk_breakdown.safety_factor || 0 }
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
                  {result.risk_breakdown.safety_factor !== undefined && (
                    <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
                      <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--accent-cyan)', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        🛡️ NIST Trust & Safety Compliance Metrics
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                        {[
                          { label: "Negation Risk", val: result.risk_breakdown.negation || 0 },
                          { label: "Harmful Bias", val: result.risk_breakdown.harmful_biasness || 0 },
                          { label: "Confabulation", val: result.risk_breakdown.confabulation || 0 },
                          { label: "Integrity Violation", val: Math.max(0, 1.0 - (result.risk_breakdown.integrity !== undefined ? result.risk_breakdown.integrity : 1)) },
                          { label: "Abusive Content", val: result.risk_breakdown.abusive || 0 },
                          { label: "Privacy Exposure", val: Math.max(0, 1.0 - (result.risk_breakdown.privacy_enhanced !== undefined ? result.risk_breakdown.privacy_enhanced : 1)) },
                          { label: "Dangerous Intent", val: result.risk_breakdown.dangerous || 0 },
                          { label: "Violent Content", val: result.risk_breakdown.violent || 0 },
                          { label: "Environmental Footprint", val: result.risk_breakdown.environmental_impacts || 0 }
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
              </div>
            )}
            
            {result.matched_policies && result.matched_policies.length > 0 && (
              <div className="policy-results-box fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div className="result-details-title" style={{ color: 'var(--status-warning)', fontWeight: '600' }}>Matched Governance Policies:</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {result.matched_policies.map((policyName, idx) => (
                    <div key={idx} style={{
                      padding: '12px',
                      background: 'rgba(245, 158, 11, 0.04)',
                      border: '1px solid rgba(245, 158, 11, 0.15)',
                      borderRadius: 'var(--border-radius-sm)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}>
                      <strong style={{ color: 'var(--status-warning)', fontSize: '14px' }}>🛡️ {policyName}</strong>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{result.violations[idx]}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="result-alert-box">
              <span className="alert-box-icon">ℹ️</span>
              <p className="alert-box-text">
                {result.status === 'AWAITING_CLARIFICATION' 
                  ? 'This action has been logged but requires further details before evaluation can conclude.'
                  : result.matched_policies && result.matched_policies.length > 0
                    ? 'Policy evaluation complete. Violations have been registered. Appropriate review constraints have been applied.'
                    : 'Action registered successfully. Policy checks completed with no policy exceptions triggered.'}
              </p>
            </div>

            {result.autonomy_level === 'USER_CONFIRMATION' && result.status === 'PENDING' && (
              <div className="confirm-action-box fade-in" style={{
                marginTop: '16px',
                padding: '16px',
                background: 'rgba(234, 179, 8, 0.05)',
                border: '1px solid rgba(234, 179, 8, 0.2)',
                borderRadius: 'var(--border-radius-sm)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <div style={{ fontSize: '14px', color: 'var(--status-warning)', fontWeight: '600' }}>
                  ⚠️ User Confirmation Required
                </div>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
                  This action is safe to proceed under your supervision. Please confirm to execute or cancel to reject.
                </p>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button 
                    onClick={async () => {
                      try {
                        const res = await api.post('/actions/confirm', { action_id: result.id });
                        setResult(res.data);
                        alert("Action successfully confirmed and executed!");
                      } catch (err) {
                        alert(err.response?.data?.detail || "Failed to confirm action");
                      }
                    }} 
                    className="btn btn-primary btn-sm"
                    style={{ background: 'var(--status-success)', borderColor: 'var(--status-success)', color: 'white', padding: '6px 12px', fontSize: '12px', border: '1px solid transparent', cursor: 'pointer', borderRadius: '4px' }}
                  >
                    Confirm & Execute ✓
                  </button>
                  <button 
                    onClick={async () => {
                      try {
                        const res = await api.post('/actions/reject', { action_id: result.id });
                        setResult(res.data);
                        alert("Action successfully cancelled.");
                      } catch (err) {
                        alert(err.response?.data?.detail || "Failed to reject action");
                      }
                    }} 
                    className="btn btn-secondary btn-sm"
                    style={{ background: 'var(--status-danger)', borderColor: 'var(--status-danger)', color: 'white', padding: '6px 12px', fontSize: '12px', border: '1px solid transparent', cursor: 'pointer', borderRadius: '4px' }}
                  >
                    Cancel Action ✗
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Historical Intelligence Card */}
          {result.history_intelligence && result.history_intelligence.total_cases > 0 && (
            <div className="glass-panel history-section fade-in" style={{ borderLeft: '4px solid var(--accent-cyan)', textAlign: 'left' }}>
              <div className="result-header" style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px', marginBottom: '16px' }}>
                <h3>Historical Intelligence</h3>
                <span className="badge badge-info">Matching Past Cases: {result.history_intelligence.total_cases}</span>
              </div>
              
              <div className="result-grid" style={{ marginBottom: '20px' }}>
                <div className="result-item" style={{ borderLeft: '3px solid var(--status-success)' }}>
                  <span className="result-label">Approval Rate</span>
                  <span className="result-val" style={{ color: 'var(--status-success)' }}>
                    {Math.round(result.history_intelligence.approval_rate * 100)}%
                  </span>
                </div>
                
                <div className="result-item" style={{ borderLeft: '3px solid var(--status-danger)' }}>
                  <span className="result-label">Rejection Rate</span>
                  <span className="result-val" style={{ color: 'var(--status-danger)' }}>
                    {Math.round(result.history_intelligence.rejection_rate * 100)}%
                  </span>
                </div>

                <div className="result-item">
                  <span className="result-label">Historic Avg Risk</span>
                  <span className="result-val">
                    {result.history_intelligence.average_risk} / 100
                  </span>
                </div>
              </div>

              {result.history_intelligence.similar_cases && result.history_intelligence.similar_cases.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div className="result-details-title">Similar Past Actions:</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {result.history_intelligence.similar_cases.map((c) => (
                      <div key={c.id} style={{
                        padding: '12px',
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: 'var(--border-radius-sm)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Case #{c.id}</span>
                          <span className={`badge ${c.status === 'APPROVED' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '11px', padding: '2px 8px' }}>
                            {c.status}
                          </span>
                        </div>
                        <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontStyle: 'italic' }}>"{c.natural_language_request}"</span>
                        {c.comments && (
                          <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                            <strong>Reviewer:</strong> {c.comments}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Clarification Questionnaire Panel */}
          {result.status === 'AWAITING_CLARIFICATION' && clarificationQuestions.length > 0 && (
            <div className="glass-panel questionnaire-section fade-in">
              <div className="questionnaire-header">
                <h3>Clarification Questionnaire</h3>
                <span className="badge badge-warning">Required</span>
              </div>
              <p className="questionnaire-sub">
                Please provide the missing details below to satisfy security context rules.
              </p>
              
              <form onSubmit={handleAnswerSubmit} className="questionnaire-form">
                {clarificationQuestions.map((q) => (
                  <div key={q.id} className="input-group">
                    <label className="input-label" htmlFor={`q-${q.id}`}>{q.question_text}</label>
                    <input
                      id={`q-${q.id}`}
                      type="text"
                      className="input-field"
                      placeholder="Type details here..."
                      value={answers[q.id] || ''}
                      onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                      disabled={submittingAnswers}
                    />
                  </div>
                ))}
                
                <button type="submit" className="btn btn-primary" disabled={submittingAnswers}>
                  {submittingAnswers ? 'Submitting Answers...' : 'Submit Answers 💾'}
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      <style>{`
        .submit-action-container {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 32px;
          align-items: start;
        }

        @media (max-width: 1024px) {
          .submit-action-container {
            grid-template-columns: 1fr;
          }
        }

        .form-section h2 {
          font-size: 22px;
          margin-bottom: 8px;
          text-align: left;
        }

        .subtitle {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 24px;
          text-align: left;
        }

        .alert {
          border-radius: var(--border-radius-sm);
          padding: 12px 16px;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 12px;
          text-align: left;
        }
        
        .alert-danger {
          background: var(--status-danger-bg);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: var(--status-danger);
          font-size: 14px;
          font-weight: 500;
        }

        .action-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .textarea-field {
          resize: vertical;
          min-height: 100px;
        }

        /* Result Section styling */
        .result-section {
          border-color: rgba(6, 182, 212, 0.2);
          display: flex;
          flex-direction: column;
          gap: 20px;
          text-align: left;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--glass-border);
          padding-bottom: 16px;
        }

        .result-header h3 {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .result-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
        }

        .result-item {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding: 12px 16px;
          background: rgba(255, 255, 255, 0.01);
          border: 1px solid var(--glass-border);
          border-radius: var(--border-radius-sm);
        }

        .result-label {
          font-size: 12px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          font-weight: 500;
        }

        .result-val {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .risk-value {
          font-size: 20px;
          font-weight: 700;
        }

        .result-details {
          padding: 16px;
          background: rgba(15, 23, 42, 0.4);
          border-radius: var(--border-radius-sm);
          border: 1px solid var(--glass-border);
        }

        .result-details-title {
          font-size: 13px;
          color: var(--text-muted);
          font-weight: 500;
          margin-bottom: 6px;
        }

        .request-quote {
          font-size: 15px;
          font-style: italic;
          color: var(--text-primary);
          line-height: 1.5;
        }

        .result-alert-box {
          display: flex;
          gap: 12px;
          padding: 14px;
          background: var(--status-info-bg);
          border: 1px solid rgba(59, 130, 246, 0.15);
          border-radius: var(--border-radius-sm);
          align-items: flex-start;
        }

        .alert-box-icon {
          font-size: 18px;
        }

        .alert-box-text {
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.5;
        }

        /* Questionnaire Section */
        .questionnaire-section {
          border-color: rgba(245, 158, 11, 0.3);
          text-align: left;
        }
        
        .questionnaire-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .questionnaire-header h3 {
          font-size: 18px;
          color: var(--text-primary);
        }
        
        .questionnaire-sub {
          font-size: 14px;
          color: var(--text-secondary);
          margin-bottom: 20px;
        }
        
        .questionnaire-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
      `}</style>
    </div>
  );
};

export default SubmitAction;
