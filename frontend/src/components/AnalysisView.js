import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function AnalysisView() {
  const [scanResult, setScanResult] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedResult = localStorage.getItem('scanResult');
    if (storedResult) {
      setScanResult(JSON.parse(storedResult));
    } else {
      navigate('/');
    }
  }, [navigate]);

  if (!scanResult) return null;

  const { brief_summary, llm_results, pattern_results, recommendations } = scanResult;

  return (
    <div style={{ padding: 20, maxWidth: '1200px', margin: '0 auto' }}>
      <h1>Detailed Analysis</h1>

      {/* Summary */}
      <section style={{ marginBottom: 30 }}>
        <h2>🔍 Summary</h2>
        <p style={{ backgroundColor: '#e2e3e5', padding: 10, borderRadius: 4 }}>
          {brief_summary || 'No summary available.'}
        </p>
      </section>

      {/* Vulnerabilities */}
      <section style={{ marginBottom: 30 }}>
        <h2>🚨 Vulnerabilities Found</h2>
        {llm_results?.vulnerabilities && llm_results.vulnerabilities.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th style={thStyle}>Type</th>
                <th style={thStyle}>Location</th>
                <th style={thStyle}>Severity</th>
                <th style={thStyle}>Description</th>
              </tr>
            </thead>
            <tbody>
              {llm_results.vulnerabilities.map((vuln, idx) => (
                <tr key={idx}>
                  <td style={tdStyle}>{vuln.type}</td>
                  <td style={tdStyle}>{vuln.location}</td>
                  <td style={tdStyle}>{vuln.severity}</td>
                  <td style={tdStyle}>{vuln.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No vulnerabilities found.</p>
        )}
      </section>

      {/* Recommendations */}
      <section style={{ marginBottom: 30 }}>
        <h2>🛡️ Recommendations</h2>
        {recommendations && recommendations.length > 0 ? (
          recommendations.map((rec, idx) => (
            <div key={idx} style={{ backgroundColor: '#f8f9fa', padding: 15, borderRadius: 6, marginBottom: 20 }}>
              <h3>{rec.vulnerability_type}</h3>
              <p><strong>Recommendation:</strong> {rec.recommendation}</p>
              <p><strong>Example:</strong> <code>{rec.code_example}</code></p>
              {rec.resources && rec.resources.length > 0 && (
                <div>
                  <strong>Resources:</strong>
                  <ul>
                    {rec.resources.map((link, idx2) => (
                      <li key={idx2}><a href={link} target="_blank" rel="noopener noreferrer">{link}</a></li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))
        ) : (
          <p>No recommendations available.</p>
        )}
      </section>

      {/* Pattern Matches (optional) */}
      <section style={{ marginBottom: 30 }}>
        <h2>🛠️ Pattern Matches</h2>
        {pattern_results && Object.keys(pattern_results).length > 0 ? (
          Object.entries(pattern_results).map(([type, matches], idx) => (
            <div key={idx} style={{ marginBottom: 20 }}>
              <h4>{type}</h4>
              <ul>
                {matches.map((match, matchIdx) => (
                  <li key={matchIdx}>
                    <strong>Line {match.line}</strong>: {match.match}
                    <pre style={{ background: '#efefef', padding: 8, borderRadius: 4 }}>{match.context}</pre>
                  </li>
                ))}
              </ul>
            </div>
          ))
        ) : (
          <p>No pattern matches found.</p>
        )}
      </section>

      {/* Back Button */}
      <div style={{ textAlign: 'center', marginTop: 40 }}>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer'
          }}
        >
          🔙 Back to Upload
        </button>
      </div>
    </div>
  );
}

const thStyle = {
  padding: '10px',
  textAlign: 'left',
  borderBottom: '1px solid #ccc'
};

const tdStyle = {
  padding: '10px',
  borderBottom: '1px solid #eee'
};

export default AnalysisView;
