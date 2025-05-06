import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/AnalysisView.css'; // Ensure correct path

function AnalysisView() {
  const [scanResult, setScanResult] = useState(null);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [securityQuestion, setSecurityQuestion] = useState('');
  const [answerLoading, setAnswerLoading] = useState(false);
  const [answerError, setAnswerError] = useState('');
  const [answerChunks, setAnswerChunks] = useState([]);

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

  const { brief_summary, llm_results, pattern_results, recommendations, file_content, remediated_file_content } = scanResult;

  // ✅ Function to highlight matches in uploaded code
  const getHighlightedCode = () => {
    if (!file_content || !pattern_results) return file_content;

    let highlighted = file_content;
    const allMatches = Object.values(pattern_results).flat().map(p => p.match);

    allMatches.sort((a, b) => b.length - a.length);

    const escapeRegex = str => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    allMatches.forEach(match => {
      const regex = new RegExp(escapeRegex(match), 'g');
      highlighted = highlighted.replace(regex, `<mark>${match}</mark>`);
    });

    return highlighted;
  };

  // ✅ Function to highlight the changed parts in remediated code
  const getHighlightedRemediatedCode = () => {
    if (!file_content || !remediated_file_content) return remediated_file_content;

    // Compare original and remediated line by line
    const originalLines = file_content.split('\n');
    const remediatedLines = remediated_file_content.split('\n');

    return remediatedLines.map((line, idx) => {
      const isDifferent = originalLines[idx] !== line;
      return isDifferent
        ? `<mark>${line}</mark>`
        : line;
    }).join('\n');
  };

  return (
    <div className="analysis-container">
      <h1 className="page-title">Detailed Analysis</h1>

      {/* Summary */}
      <section className="card-section">
        <div className="card">
          <h2>🔍 Summary</h2>
          <p className="summary-box">{brief_summary || 'No summary available.'}</p>
        </div>
      </section>

      {/* Uploaded Code */}
      <section className="card-section uploaded-code">
        <div className="card">
          <h2>📄 Uploaded Code</h2>
          {file_content ? (
            <pre
              style={{
                backgroundColor: '#0f172a',
                padding: '15px',
                borderRadius: '8px',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                maxHeight: '500px',
                overflowY: 'auto',
              }}
              dangerouslySetInnerHTML={{ __html: getHighlightedCode() }}
            />
          ) : (
            <p>No uploaded code available.</p>
          )}
        </div>
      </section>

      {/* Pattern Matches */}
      <section className="card-section">
        <div className="card">
          <h2>Pattern Matches</h2>
          {pattern_results && Object.keys(pattern_results).length > 0 ? (
            Object.entries(pattern_results).map(([type, matches], idx) => (
              <div key={idx} className="pattern-box">
                <h4>{type}</h4>
                <ul>
                  {matches.map((match, matchIdx) => (
                    <li key={matchIdx} style={{ marginBottom: '12px' }}>
                      <strong>Match:</strong> {match.match} <br />
                      <strong>Line:</strong> {match.line} <br />
                      <strong>Pattern:</strong> {match.pattern} <br />
                      <strong>Context:</strong>
                      <pre
                        style={{
                          backgroundColor: '#1e293b',
                          padding: '8px',
                          borderRadius: '4px',
                          overflowX: 'auto',
                          whiteSpace: 'pre-wrap',
                          marginTop: '5px',
                        }}
                      >
                        {match.context}
                      </pre>
                    </li>
                  ))}
                </ul>
              </div>
            ))
          ) : (
            <p>No pattern matches found.</p>
          )}
        </div>
      </section>

      {/* Vulnerabilities Found */}
      <section className="card-section">
        <div className="card">
          <h2>Vulnerabilities Found</h2>
          {llm_results?.vulnerabilities && llm_results.vulnerabilities.length > 0 ? (
            <table className="vuln-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Severity</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {llm_results.vulnerabilities.map((vuln, idx) => (
                  <tr key={idx} className={`severity-${vuln.severity?.toLowerCase()}`}>
                    <td>{vuln.type}</td>
                    <td>{vuln.location}</td>
                    <td>{vuln.severity}</td>
                    <td>{vuln.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No vulnerabilities found.</p>
          )}
        </div>
      </section>

      {/* 💡 Suggested Fix  */}
      <section className="card-section cleaned-code">
        <div className="card">
          <h2>💡 Suggested Fix</h2>
          {remediated_file_content ? (
            <pre
              style={{
                backgroundColor: '#0f172a',
                padding: '15px',
                borderRadius: '8px',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                maxHeight: '500px',
                overflowY: 'auto',
              }}
              dangerouslySetInnerHTML={{ __html: getHighlightedRemediatedCode() }}
            />
          ) : (
            <p>No suggested fix available.</p>
          )}
        </div>
      </section>

      {/* Recommendations */}
      <section className="card-section">
        <div className="card">
          <h2>🛡️ Recommendations</h2>
          {recommendations && recommendations.length > 0 ? (
            recommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-box">
                <h3>{rec.vulnerability_type}</h3>
                <p><strong>Recommendation:</strong> {rec.recommendation}</p>
                <p><strong>Example:</strong> <code>{rec.code_example}</code></p>
                {rec.resources && rec.resources.length > 0 && (
                  <div>
                    <strong>Resources:</strong>
                    <ul>
                      {rec.resources.map((link, idx2) => (
                        <li key={idx2}>
                          <a href={link} target="_blank" rel="noopener noreferrer">{link}</a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          ) : (
            <p>No recommendations available.</p>
          )}
        </div>
      </section>

      {/* Buttons */}
      <div className="button-group">
        <button className="btn btn-back" onClick={() => navigate('/')}>🔙 Back to Upload</button>
        <button className="btn btn-question" onClick={() => setShowQuestionModal(true)}>Ask a Security Question</button>
      </div>

      {/* Modal */}
      {showQuestionModal && (
        <div className="modal-overlay fade-in">
          <div className="modal-content">
            <h2>Ask a Security Question</h2>
            <textarea
              className="question-input"
              value={securityQuestion}
              onChange={(e) => setSecurityQuestion(e.target.value)}
              placeholder="Type your question here..."
            />

            <div className="modal-actions" style={{ justifyContent: 'center' }}>
              <button
                className="btn btn-submit"
                onClick={async () => {
                  setAnswerLoading(true);
                  setAnswerError('');
                  setAnswerChunks([]);

                  try {
                    const response = await fetch('http://localhost:5000/rag_explanation', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ query: securityQuestion }),
                    });

                    const data = await response.json();

                    if (data.error) {
                      setAnswerError(`${data.error}`);
                    } else if (!data.chunks || data.chunks.length === 0) {
                      setAnswerError('No relevant information found.');
                    } else {
                      setAnswerChunks(data.chunks);
                    }
                  } catch (err) {
                    setAnswerError('Failed to connect to the server.');
                  } finally {
                    setAnswerLoading(false);
                  }
                }}
              >
                Submit
              </button>
              <button
                className="btn btn-cancel"
                onClick={() => {
                  setShowQuestionModal(false);
                  setSecurityQuestion('');
                  setAnswerChunks([]);
                  setAnswerError('');
                  setAnswerLoading(false);
                }}
              >
                Cancel
              </button>
            </div>

            <div className="answer-section" style={{ maxHeight: '350px', overflowY: 'auto' }}>
              {answerLoading && <p>Loading...</p>}
              {answerError && <p style={{ color: 'red' }}>{answerError}</p>}
              {answerChunks.length > 0 &&
                answerChunks.map((chunk, idx) => (
                  <div key={idx} style={{ marginBottom: '15px', borderBottom: '1px solid #475569' }}>
                    {chunk}
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnalysisView;
