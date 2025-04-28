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
    <div style={{ padding: 20, maxWidth: '800px', margin: '0 auto' }}>
      <h1>Vulnerability Scanner</h1>

      <div style={{ backgroundColor: serverStatus === 'Connected' ? '#d4edda' : '#f8d7da', padding: 10, marginBottom: 20, borderRadius: 4 }}>
        Server Status: {serverStatus}
      </div>

      <div style={{ marginBottom: 20 }}>
        <input type="file" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={loading || !file} style={{ marginLeft: 10 }}>
          {loading ? 'Uploading...' : 'Upload and Scan'}
        </button>
      </div>

      {error && (
        <div style={{ backgroundColor: '#f8d7da', padding: 10, borderRadius: 4, marginBottom: 20 }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {scanResult && (
        <div style={{ marginTop: 30 }}>
          <h2>Brief Summary</h2>
          <p style={{ backgroundColor: '#e2e3e5', padding: 10, borderRadius: 4 }}>
            {scanResult.brief_summary || "No summary available."}
          </p>

          <button onClick={handleDeepAnalysis} disabled={deepLoading} style={{ marginTop: 10, marginLeft: 10 }}>
            {deepLoading ? 'Requesting Deep Analysis...' : 'Request Deeper Analysis'}
          </button>
        </div>
      )}
    </div>
  );
}

export default FileUpload;
