import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function FileUpload() {
  const [file, setFile] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [deepLoading, setDeepLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState('Checking...');
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      await axios.get('http://localhost:5000/test');
      setServerStatus('Connected');
    } catch (error) {
      console.error('Server status check failed:', error);
      setServerStatus('Not connected');
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => setDragActive(false);

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file!');
      return;
    }

    setLoading(true);
    setError(null);
    setScanResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      console.log('Scan Result:', response.data);
      setScanResult(response.data);
      localStorage.setItem('scanResult', JSON.stringify(response.data));
    } catch (error) {
      console.error('Upload failed:', error);
      setError('Error uploading file.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeepAnalysis = async () => {
    if (!scanResult) return;
    setDeepLoading(true);

    try {
      const code = scanResult.llm_results?.summary || "Unable to extract code";
      const response = await axios.post('http://localhost:5000/deep_analysis', { code });

      console.log('Deep Analysis Result:', response.data);
      localStorage.setItem('deepAnalysis', JSON.stringify(response.data));
      navigate('/analysis');
    } catch (error) {
      console.error('Deep analysis failed:', error);
      setError('Error requesting deeper analysis.');
    } finally {
      setDeepLoading(false);
    }
  };

  return (
    <div style={{ padding: 30, maxWidth: '800px', margin: '0 auto', color: '#fff', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ textAlign: 'center', marginBottom: 20 }}>🛡️ Vulnerability Scanner</h1>

      <div style={{ backgroundColor: serverStatus === 'Connected' ? '#14532d' : '#7f1d1d', padding: 10, borderRadius: 6, marginBottom: 20, textAlign: 'center' }}>
        Server Status: {serverStatus}
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{
          border: dragActive ? '2px dashed #3b82f6' : '2px dashed #666',
          padding: '30px',
          borderRadius: '10px',
          textAlign: 'center',
          marginBottom: '20px',
          backgroundColor: dragActive ? '#1e293b' : '#111827',
        }}
      >
        <p>{file ? `Selected: ${file.name}` : 'Drag & drop your file here or click to browse'}</p>
        <input type="file" onChange={handleFileChange} style={{ marginTop: 10 }} />
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={handleUpload}
          disabled={loading || !file}
          style={{
            backgroundColor: '#2563eb',
            color: '#fff',
            padding: '10px 20px',
            border: 'none',
            borderRadius: 5,
            cursor: loading || !file ? 'not-allowed' : 'pointer',
            opacity: loading || !file ? 0.6 : 1,
          }}
        >
          {loading ? 'Uploading...' : 'Upload and Scan'}
        </button>
      </div>

      {error && (
        <div style={{ backgroundColor: '#7f1d1d', padding: 10, borderRadius: 6, marginTop: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {scanResult && (
        <div style={{ marginTop: 30 }}>
          <h2>🧠 Brief Summary</h2>
          <p style={{ backgroundColor: '#334155', padding: 10, borderRadius: 6 }}>
            {scanResult.brief_summary || "No summary available."}
          </p>

          <button
            onClick={handleDeepAnalysis}
            disabled={deepLoading}
            style={{
              marginTop: 10,
              backgroundColor: '#10b981',
              color: '#fff',
              padding: '10px 20px',
              border: 'none',
              borderRadius: 5,
              cursor: deepLoading ? 'not-allowed' : 'pointer',
              opacity: deepLoading ? 0.6 : 1,
            }}
          >
            {deepLoading ? 'Requesting Deep Analysis...' : 'Request Deeper Analysis'}
          </button>
        </div>
      )}
    </div>
  );
}

export default FileUpload;
