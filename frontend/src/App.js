import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FileUpload from './components/FileUpload';
import AnalysisView from './components/AnalysisView';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FileUpload />} />
        <Route path="/analysis" element={<AnalysisView />} />
      </Routes>
    </Router>
  );
}

export default App;