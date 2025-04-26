import React, { useState, useEffect } from 'react';
import axios from 'axios';

function FileUpload() {
  const [file, setFile] = useState(null);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState('Checking...');

  // Check if server is running when component mounts
  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await axios.get('http://localhost:5000/test');
      setServerStatus('Connected');
    } catch (error) {
      console.error('Server status check failed:', error);
      setServerStatus('Not connected - Please check if backend server is running');
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null); // Clear previous errors
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first!');
      return;
    }

    setLoading(true);
    setError(null);
    setScanResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Log request details for debugging
      console.log('Sending file:', file);
      console.log('File type:', file.type);
      console.log('File size:', file.size);

      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      console.log('Server response:', response);
      setScanResult(response.data);
    } catch (error) {
      console.error('Upload failed:', error);
      
      // Extract detailed error information
      let errorMessage = 'Unknown error occurred';
      if (error.response) {
        // The server responded with a status code outside of 2xx
        console.error('Error response:', error.response);
        errorMessage = `Server error: ${error.response.status} - ${
          error.response.data.error || error.response.data.message || 'Unknown error'
        }`;
      } else if (error.request) {
        // The request was made but no response was received
        console.error('Error request:', error.request);
        errorMessage = 'No response from server. Is the backend running?';
      } else {
        // Something happened in setting up the request
        errorMessage = `Error: ${error.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: '800px', margin: '0 auto' }}>
      <h1>Vulnerability Scanner</h1>
      
      <div style={{ 
        padding: 10, 
        marginBottom: 20, 
        backgroundColor: serverStatus === 'Connected' ? '#d4edda' : '#f8d7da',
        borderRadius: 4 
      }}>
        <strong>Server Status:</strong> {serverStatus}
        <button 
          onClick={checkServerStatus} 
          style={{ marginLeft: 10, padding: '2px 8px' }}
        >
          Refresh
        </button>
      </div>
      
      <div style={{ marginBottom: 20 }}>
        <input 
          type="file" 
          onChange={handleFileChange} 
          style={{ border: '1px solid #ccc', padding: 10, borderRadius: 4 }}
        />
        
        <button 
          onClick={handleUpload} 
          disabled={loading || !file} 
          style={{ 
            marginLeft: 10, 
            padding: '8px 16px', 
            backgroundColor: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: 4,
            cursor: loading || !file ? 'not-allowed' : 'pointer' 
          }}
        >
          {loading ? 'Uploading...' : 'Upload and Scan'}
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', margin: '20px 0' }}>
          <p>Processing file, please wait...</p>
          <div style={{ 
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #3498db',
            borderRadius: '50%',
            width: '40px',
            height: '40px',
            margin: '0 auto',
            animation: 'spin 2s linear infinite'
          }} />
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}

      {error && (
        <div style={{ 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          padding: 10, 
          borderRadius: 4,
          marginBottom: 20
        }}>
          <h3>Error:</h3>
          <p>{error}</p>
        </div>
      )}

      {scanResult && (
        <div style={{ marginTop: 30 }}>
          <h2>Scan Result</h2>
          <pre style={{ 
            background: '#f0f0f0', 
            padding: 10, 
            borderRadius: 4, 
            overflowX: 'auto' 
          }}>
            {JSON.stringify(scanResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default FileUpload;