// src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import EmployeePortal from './EmployeePortal';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <nav className="border-b">
          <div className="container mx-auto px-4 flex items-center justify-between h-14">
            <Link to="/" className="font-medium">Employee Portal</Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<EmployeePortal />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
