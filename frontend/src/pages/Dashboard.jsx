import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import api from '../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const roleName = user?.role?.name || 'Employee';

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get('/analytics');
        setData(res.data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch governance analytics:', err);
        setError('Failed to load system analytics. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
    // Poll analytics every 15 seconds to keep charts live
    const interval = setInterval(fetchAnalytics, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="spinner"></div>
        <p>Analyzing corporate AI governance metrics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-panel analytics-error-panel fade-in">
        <h3>⚠️ Analytics Unavailable</h3>
        <p>{error || 'Unexpected error occurred loading dashboard.'}</p>
        <button onClick={() => window.location.reload()} className="btn btn-primary btn-sm">
          Retry Reload 🔄
        </button>
      </div>
    );
  }

  const {
    kpis,
    risk_distribution,
    policy_violations,
    approval_trends,
    department_risk,
    monthly_statistics,
    reviewer_performance,
    llm_confidence_trend,
  } = data;

  // Helpers for custom line charts
  const getSVGLinePath = (series, key, width, height, maxVal) => {
    if (series.length < 2) return '';
    const points = series.map((item, idx) => {
      const x = (idx / (series.length - 1)) * width;
      const val = parseFloat(item[key]);
      const y = height - (val / (maxVal || 1)) * height;
      return `${x},${y}`;
    });
    return `M ${points.join(' L ')}`;
  };

  const getSVGAreaPath = (series, key, width, height, maxVal) => {
    if (series.length < 2) return '';
    const linePath = getSVGLinePath(series, key, width, height, maxVal);
    const lastX = width;
    const lastY = height;
    return `${linePath} L ${lastX},${lastY} L 0,${height} Z`;
  };

  const maxApprovalTrendVal = Math.max(
    ...approval_trends.map((t) => Math.max(t.approved, t.rejected, 1))
  );

  return (
    <div className="dashboard-container fade-in">
      {/* Welcome Banner */}
      <div className="glass-panel welcome-banner">
        <div className="welcome-text">
          <h1>Welcome back, <span className="highlight">{user?.username}</span>!</h1>
          <p>
            You are signed in as an <strong style={{ color: 'var(--accent-cyan)' }}>{roleName}</strong>. 
            The Enterprise AI Governance Platform is active and monitoring AI-generated actions.
          </p>
        </div>
        <div className="welcome-icon">🛡️</div>
      </div>

      {/* KPI Cards Row */}
      <div className="kpi-grid">
        <div className="glass-panel kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Total Requests</span>
            <span className="kpi-icon">⚡</span>
          </div>
          <div className="kpi-value">{kpis.total_requests}</div>
          <p className="kpi-sub">Total actions evaluated by platform</p>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Average Risk</span>
            <span className="kpi-icon">🛡️</span>
          </div>
          <div className={`kpi-value ${kpis.average_risk > 60 ? 'text-danger' : kpis.average_risk > 30 ? 'text-warning' : 'text-success'}`}>
            {kpis.average_risk}%
          </div>
          <p className="kpi-sub">Overall risk of AI action pool</p>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Avg Review Time</span>
            <span className="kpi-icon">⏱️</span>
          </div>
          <div className="kpi-value">{kpis.review_time_hours}h</div>
          <p className="kpi-sub">Average human review resolution time</p>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Auto Approval</span>
            <span className="kpi-icon">🤖</span>
          </div>
          <div className="kpi-value">{kpis.auto_approval_rate}%</div>
          <p className="kpi-sub">Low-risk items approved automatically</p>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Escalation Rate</span>
            <span className="kpi-icon">⚖️</span>
          </div>
          <div className="kpi-value">{kpis.escalation_rate}%</div>
          <p className="kpi-sub">High-risk actions flagged for review</p>
        </div>
      </div>

      {/* Grid of Main Analytics Charts */}
      <div className="charts-grid">
        {/* Risk Distribution Chart */}
        <div className="glass-panel chart-box">
          <h3 className="chart-title">Risk Profile Distribution</h3>
          <div className="risk-dist-chart">
            {Object.entries(risk_distribution).map(([label, count]) => {
              const maxCount = Math.max(...Object.values(risk_distribution), 1);
              const percentage = (count / maxCount) * 100;
              const barClass = label.includes('Low') ? 'bar-low' : label.includes('Medium') ? 'bar-med' : label.includes('High') ? 'bar-high' : 'bar-crit';
              
              return (
                <div key={label} className="risk-dist-bar-wrapper">
                  <div className="risk-dist-bar-container">
                    <div 
                      className={`risk-dist-bar ${barClass}`} 
                      style={{ height: `${percentage}%` }}
                    >
                      <span className="bar-count-tag">{count}</span>
                    </div>
                  </div>
                  <span className="risk-dist-label">{label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Approval Trends Chart */}
        <div className="glass-panel chart-box">
          <h3 className="chart-title">Weekly Approval vs Rejection Trend</h3>
          <div className="svg-chart-container" style={{ position: 'relative', height: '200px' }}>
            {approval_trends.length > 1 ? (
              <svg viewBox="0 0 500 200" width="100%" height="100%" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="approved-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--status-success)" stopOpacity="0.25"/>
                    <stop offset="100%" stopColor="var(--status-success)" stopOpacity="0.0"/>
                  </linearGradient>
                  <linearGradient id="rejected-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--status-danger)" stopOpacity="0.25"/>
                    <stop offset="100%" stopColor="var(--status-danger)" stopOpacity="0.0"/>
                  </linearGradient>
                </defs>

                {/* Area paths */}
                <path d={getSVGAreaPath(approval_trends, 'approved', 500, 200, maxApprovalTrendVal)} fill="url(#approved-grad)" />
                <path d={getSVGAreaPath(approval_trends, 'rejected', 500, 200, maxApprovalTrendVal)} fill="url(#rejected-grad)" />

                {/* Lines */}
                <path d={getSVGLinePath(approval_trends, 'approved', 500, 200, maxApprovalTrendVal)} fill="none" stroke="var(--status-success)" strokeWidth="2.5" />
                <path d={getSVGLinePath(approval_trends, 'rejected', 500, 200, maxApprovalTrendVal)} fill="none" stroke="var(--status-danger)" strokeWidth="2.5" strokeDasharray="4 2" />

                {/* Gridlines */}
                <line x1="0" y1="50" x2="500" y2="50" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="0" y1="100" x2="500" y2="100" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="0" y1="150" x2="500" y2="150" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
              </svg>
            ) : (
              <div className="no-data-msg">Gathering daily stats...</div>
            )}
            <div className="chart-legend">
              <span className="legend-item"><span className="legend-dot green"></span>Approved</span>
              <span className="legend-item"><span className="legend-dot red"></span>Rejected</span>
            </div>
            <div className="chart-x-labels">
              {approval_trends.map((item, idx) => (
                <span key={idx}>{item.date}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Department-wise Risk (Domain-wise) */}
        <div className="glass-panel chart-box">
          <h3 className="chart-title">Risk Metrics by Business Domain</h3>
          <div className="domain-risk-container">
            {department_risk.map((dom) => (
              <div key={dom.department} className="domain-risk-card">
                <span className="domain-name">{dom.department}</span>
                <div className="circular-progress-wrapper">
                  <svg className="radial-progress-svg" viewBox="0 0 36 36">
                    <path
                      className="radial-bg"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className={`radial-fill ${dom.average_risk > 60 ? 'high' : dom.average_risk > 30 ? 'med' : 'low'}`}
                      strokeDasharray={`${dom.average_risk}, 100`}
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="radial-value-label">{dom.average_risk}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* LLM Confidence Trend Chart */}
        <div className="glass-panel chart-box">
          <h3 className="chart-title">LLM Intent Extraction Confidence</h3>
          <div className="svg-chart-container" style={{ position: 'relative', height: '200px' }}>
            {llm_confidence_trend.length > 1 ? (
              <svg viewBox="0 0 500 200" width="100%" height="100%" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="cyan-glow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.25"/>
                    <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0.0"/>
                  </linearGradient>
                  <filter id="neon-glow-filter" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                <path d={getSVGAreaPath(llm_confidence_trend, 'confidence', 500, 200, 1.0)} fill="url(#cyan-glow)" />
                <path d={getSVGLinePath(llm_confidence_trend, 'confidence', 500, 200, 1.0)} fill="none" stroke="var(--accent-cyan)" strokeWidth="3" filter="url(#neon-glow-filter)" />
                
                {/* Confidence threshold line (0.80) */}
                <line x1="0" y1="40" x2="500" y2="40" stroke="rgba(255,255,255,0.15)" strokeWidth="1" strokeDasharray="3 3" />
              </svg>
            ) : (
              <div className="no-data-msg">Syncing confidence trend...</div>
            )}
            <div className="chart-legend">
              <span className="legend-item"><span className="legend-dot cyan"></span>Model Confidence (Min Target: 0.8)</span>
            </div>
            <div className="chart-x-labels">
              {llm_confidence_trend.map((item, idx) => (
                <span key={idx}>{item.date}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Policy Violations Leaderboard */}
        <div className="glass-panel chart-box">
          <h3 className="chart-title">Triggered Policy Violations</h3>
          <div className="policy-violations-list">
            {Object.keys(policy_violations).length === 0 ? (
              <div className="no-violations">No active policy violations logged. ✅</div>
            ) : (
              Object.entries(policy_violations)
                .sort((a, b) => b[1] - a[1])
                .map(([name, count]) => (
                  <div key={name} className="policy-violation-row">
                    <div className="policy-row-label">
                      <span className="policy-badge">⚠️</span>
                      <span className="policy-name-txt">{name}</span>
                    </div>
                    <div className="policy-bar-progress-container">
                      <div className="policy-progress-bg">
                        <div 
                          className="policy-progress-fill" 
                          style={{ width: `${Math.min((count / 10) * 100, 100)}%` }}
                        ></div>
                      </div>
                      <span className="policy-violation-count">{count} triggers</span>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>

        {/* Stacked Monthly Stats */}
        <div className="glass-panel chart-box">
          <h3 className="chart-title">Monthly Governance Statistics</h3>
          <div className="monthly-stats-chart">
            {monthly_statistics.map((m) => {
              const maxVal = Math.max(...monthly_statistics.map((item) => item.total), 1);
              const approvedPercentage = (m.approved / maxVal) * 100;
              const rejectedPercentage = (m.rejected / maxVal) * 100;
              
              return (
                <div key={m.month} className="monthly-stat-column-wrapper">
                  <div className="monthly-column-container">
                    <div className="monthly-column-bar-group">
                      <div 
                        className="monthly-bar approved" 
                        style={{ height: `${approvedPercentage}%` }}
                        title={`Approved: ${m.approved}`}
                      ></div>
                      <div 
                        className="monthly-bar rejected" 
                        style={{ height: `${rejectedPercentage}%` }}
                        title={`Rejected: ${m.rejected}`}
                      ></div>
                    </div>
                  </div>
                  <span className="monthly-label">{m.month}</span>
                </div>
              );
            })}
          </div>
          <div className="chart-legend" style={{ marginTop: '12px' }}>
            <span className="legend-item"><span className="legend-dot green"></span>Approved</span>
            <span className="legend-item"><span className="legend-dot red"></span>Rejected</span>
          </div>
        </div>
      </div>

      {/* Reviewers and Quick Actions */}
      <div className="grid-cols-2 lower-sections">
        {/* Reviewer Performance */}
        <div className="glass-panel leaderboard-section">
          <h3 className="section-title">Reviewer Action Performance</h3>
          <div className="leaderboard-list">
            {reviewer_performance.length === 0 ? (
              <div className="no-reviewers">No reviewer decision records exist yet.</div>
            ) : (
              reviewer_performance.map((rev, index) => (
                <div key={rev.reviewer} className="leaderboard-row">
                  <div className="leaderboard-rank">#{index + 1}</div>
                  <div className="leaderboard-name">{rev.reviewer}</div>
                  <div className="leaderboard-cases">{rev.resolved_cases} cases resolved</div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Guidelines Panel */}
        <div className="glass-panel guidelines-section">
          <h3 className="section-title">System Overview & Guidelines</h3>
          <p className="guideline-intro">
            Corporate governance policies enforce compliance protocols, audit trails, and human-in-the-loop review operations:
          </p>
          <ul className="guidelines-list">
            <li>Low-risk actions below 30% are automatically approved and executed.</li>
            <li>Medium-risk actions request a confirmation check from the user before executing.</li>
            <li>Critical and high-risk actions are escalated and require reviewer authorization.</li>
          </ul>
          <div className="guidelines-actions">
            {(roleName === 'Employee' || roleName === 'Administrator') && (
              <Link to="/actions/submit" className="btn btn-primary btn-sm">
                Submit New Action ⚡
              </Link>
            )}
            {(roleName === 'Governance Reviewer' || roleName === 'Administrator') && (
              <Link to="/cases" className="btn btn-primary btn-sm">
                Review Pending Cases 🛡️
              </Link>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .dashboard-container {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .welcome-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 24px 32px;
          background: linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%), var(--glass-bg);
          border-color: rgba(168, 85, 247, 0.15);
        }

        .welcome-text h1 {
          font-size: 26px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 6px;
          text-align: left;
        }

        .welcome-text p {
          font-size: 14.5px;
          color: var(--text-secondary);
          margin: 0;
          text-align: left;
        }

        .welcome-text .highlight {
          background: var(--accent-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .welcome-icon {
          font-size: 42px;
        }

        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 16px;
        }

        .kpi-card {
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          align-items: flex-start;
        }

        .kpi-header {
          display: flex;
          justify-content: space-between;
          width: 100%;
          align-items: center;
        }

        .kpi-title {
          font-size: 11.5px;
          font-weight: 600;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .kpi-icon {
          font-size: 16px;
        }

        .kpi-value {
          font-size: 32px;
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1.1;
        }

        .kpi-sub {
          font-size: 11.5px;
          color: var(--text-muted);
          margin: 0;
        }

        .charts-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
        }

        .chart-box {
          padding: 18px 20px;
          display: flex;
          flex-direction: column;
          gap: 14px;
          min-height: 270px;
        }

        .chart-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
          text-align: left;
        }

        /* Risk Dist Bar Chart */
        .risk-dist-chart {
          display: flex;
          justify-content: space-around;
          align-items: flex-end;
          flex: 1;
          height: 180px;
          padding-top: 10px;
        }

        .risk-dist-bar-wrapper {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          width: 60px;
        }

        .risk-dist-bar-container {
          height: 120px;
          width: 24px;
          background: rgba(255,255,255,0.02);
          border-radius: var(--border-radius-sm);
          display: flex;
          align-items: flex-end;
          overflow: visible;
        }

        .risk-dist-bar {
          width: 100%;
          border-radius: var(--border-radius-sm);
          transition: height 1s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          position: relative;
        }

        .bar-low {
          background: linear-gradient(to top, #06b6d4, #22d3ee);
        }

        .bar-med {
          background: linear-gradient(to top, #eab308, #fde047);
        }

        .bar-high {
          background: linear-gradient(to top, #f97316, #ffedd5);
        }

        .bar-crit {
          background: linear-gradient(to top, #ef4444, #fca5a5);
        }

        .bar-count-tag {
          position: absolute;
          top: -20px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 11px;
          color: var(--text-primary);
          font-weight: 600;
        }

        .risk-dist-label {
          font-size: 11px;
          color: var(--text-muted);
        }

        /* SVG Line charts */
        .svg-chart-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }

        .no-data-msg {
          color: var(--text-muted);
          font-size: 13px;
          align-self: center;
          margin-top: 40px;
        }

        .chart-legend {
          display: flex;
          justify-content: center;
          gap: 16px;
          font-size: 11.5px;
          color: var(--text-secondary);
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .legend-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .legend-dot.green { background: var(--status-success); }
        .legend-dot.red { background: var(--status-danger); }
        .legend-dot.cyan { background: var(--accent-cyan); }

        .chart-x-labels {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          color: var(--text-muted);
          padding: 0 4px;
        }

        /* Circular Dials Domain Risk */
        .domain-risk-container {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 10px;
          flex: 1;
          align-items: center;
        }

        .domain-risk-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 10px;
          padding: 10px 4px;
          background: rgba(255,255,255,0.01);
          border: 1px solid var(--glass-border);
          border-radius: var(--border-radius-sm);
        }

        .domain-name {
          font-size: 11px;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .circular-progress-wrapper {
          position: relative;
          width: 50px;
          height: 50px;
        }

        .radial-progress-svg {
          transform: rotate(-90deg);
          width: 100%;
          height: 100%;
        }

        .radial-bg {
          fill: none;
          stroke: rgba(255,255,255,0.03);
          stroke-width: 3.5;
        }

        .radial-fill {
          fill: none;
          stroke-width: 3.5;
          stroke-linecap: round;
          transition: stroke-dasharray 0.8s ease;
        }

        .radial-fill.low { stroke: #22d3ee; }
        .radial-fill.med { stroke: #eab308; }
        .radial-fill.high { stroke: #ef4444; }

        .radial-value-label {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: 11px;
          font-weight: 600;
          color: var(--text-primary);
        }

        /* Policy violations list */
        .policy-violations-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          flex: 1;
          justify-content: center;
        }

        .no-violations {
          font-size: 13.5px;
          color: var(--text-secondary);
          text-align: center;
          padding: 20px;
        }

        .policy-violation-row {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .policy-row-label {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .policy-badge {
          font-size: 13px;
        }

        .policy-name-txt {
          font-size: 12.5px;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .policy-bar-progress-container {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .policy-progress-bg {
          flex: 1;
          height: 6px;
          background: rgba(255,255,255,0.03);
          border-radius: 3px;
          overflow: hidden;
        }

        .policy-progress-fill {
          height: 100%;
          background: linear-gradient(to right, var(--status-warning), var(--status-danger));
          border-radius: 3px;
          transition: width 0.8s ease;
        }

        .policy-violation-count {
          font-size: 11.5px;
          color: var(--text-muted);
          min-width: 60px;
          text-align: right;
        }

        /* Stacked columns Monthly Stats */
        .monthly-stats-chart {
          display: flex;
          justify-content: space-around;
          align-items: flex-end;
          flex: 1;
          height: 160px;
          padding-top: 10px;
        }

        .monthly-stat-column-wrapper {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          width: 80px;
        }

        .monthly-column-container {
          height: 100px;
          width: 32px;
          display: flex;
          align-items: flex-end;
          background: rgba(255,255,255,0.01);
          border-radius: var(--border-radius-sm);
        }

        .monthly-column-bar-group {
          width: 100%;
          display: flex;
          flex-direction: column-reverse;
          align-items: center;
        }

        .monthly-bar {
          width: 100%;
          transition: height 0.8s ease;
        }

        .monthly-bar.approved {
          background: linear-gradient(to top, rgba(34, 197, 94, 0.4), rgba(74, 222, 128, 0.7));
          border-top-left-radius: var(--border-radius-sm);
          border-top-right-radius: var(--border-radius-sm);
        }

        .monthly-bar.rejected {
          background: linear-gradient(to top, rgba(239, 68, 68, 0.4), rgba(248, 113, 113, 0.7));
          border-bottom-left-radius: var(--border-radius-sm);
          border-bottom-right-radius: var(--border-radius-sm);
        }

        .monthly-label {
          font-size: 10px;
          color: var(--text-muted);
        }

        /* Reviewer leaderboard and guidelines */
        .lower-sections {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
          margin-top: 8px;
        }

        .leaderboard-section, .guidelines-section {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          min-height: 220px;
          align-items: flex-start;
          text-align: left;
        }

        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
        }

        .leaderboard-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
          width: 100%;
        }

        .no-reviewers {
          font-size: 13.5px;
          color: var(--text-muted);
          padding: 20px 0;
        }

        .leaderboard-row {
          display: flex;
          align-items: center;
          padding: 10px 12px;
          background: rgba(255,255,255,0.01);
          border: 1px solid var(--glass-border);
          border-radius: var(--border-radius-sm);
          width: 100%;
        }

        .leaderboard-rank {
          font-size: 13px;
          font-weight: 700;
          color: var(--accent-cyan);
          width: 32px;
        }

        .leaderboard-name {
          font-size: 13.5px;
          color: var(--text-primary);
          flex: 1;
          font-weight: 500;
        }

        .leaderboard-cases {
          font-size: 12.5px;
          color: var(--text-secondary);
        }

        .guideline-intro {
          font-size: 13.5px;
          color: var(--text-secondary);
          line-height: 1.5;
          margin: 0;
        }

        .guidelines-list {
          margin: 0;
          padding-left: 20px;
          font-size: 13px;
          color: var(--text-secondary);
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .guidelines-actions {
          display: flex;
          gap: 12px;
          margin-top: 10px;
        }

        .analytics-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 80px 0;
          color: var(--text-secondary);
          gap: 16px;
        }

        .spinner {
          width: 36px;
          height: 36px;
          border: 3px solid rgba(255,255,255,0.05);
          border-top-color: var(--accent-cyan);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .analytics-error-panel {
          padding: 40px;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
