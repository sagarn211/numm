import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Materials } from './pages/Materials';
import { ImportMaterials } from './pages/ImportMaterials';
import { AIRecommendations } from './pages/AIRecommendations';
import { MaterialComparison } from './pages/MaterialComparison';
import { NationalMaterials } from './pages/NationalMaterials';
import { Approvals } from './pages/Approvals';
import { AuditTrail } from './pages/AuditTrail';

import { useAuth } from './hooks/useAuth';

// Protected Route Wrapper Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Public Only Route Wrapper (e.g. Login page when already logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login */}
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />

          {/* Protected Application Workspace */}
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="materials" element={<Materials />} />
            <Route path="import" element={<ImportMaterials />} />
            <Route path="ai-recommendations" element={<AIRecommendations />} />
            <Route path="comparison" element={<MaterialComparison />} />
            <Route path="national-materials" element={<NationalMaterials />} />
            <Route path="approvals" element={<Approvals />} />
            <Route path="audit-trail" element={<AuditTrail />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
