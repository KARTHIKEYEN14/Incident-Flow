import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import CreateIncident from './pages/CreateIncident';
import IncidentRoom from './pages/IncidentRoom';
import { api } from './lib/api';
import type { ReactNode } from 'react';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = api.getToken();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/incidents/new" 
            element={
              <ProtectedRoute>
                <CreateIncident />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/incidents/:id" 
            element={
              <ProtectedRoute>
                <IncidentRoom />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
