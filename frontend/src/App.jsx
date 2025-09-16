import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import Homepage from './components/Homepage';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Default route is now the Login page */}
          <Route path="/" element={<LoginForm />} />
          
          {/* The Dashboard/Homepage is now a protected route */}
          <Route path="/dashboard" element={<Homepage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
