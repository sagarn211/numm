import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { useAuth } from './hooks/useAuth';
import { hasPermission } from './utils/permissions';

const Login = lazy(() => import('./pages/Login').then(module => ({ default: module.Login })));
const Dashboard = lazy(() => import('./pages/Dashboard').then(module => ({ default: module.Dashboard })));
const Materials = lazy(() => import('./pages/Materials').then(module => ({ default: module.Materials })));
const ImportMaterials = lazy(() => import('./pages/ImportMaterials').then(module => ({ default: module.ImportMaterials })));
const AIRecommendations = lazy(() => import('./pages/AIRecommendations').then(module => ({ default: module.AIRecommendations })));
const MaterialComparison = lazy(() => import('./pages/MaterialComparison').then(module => ({ default: module.MaterialComparison })));
const NationalMaterials = lazy(() => import('./pages/NationalMaterials').then(module => ({ default: module.NationalMaterials })));
const Approvals = lazy(() => import('./pages/Approvals').then(module => ({ default: module.Approvals })));
const AuditTrail = lazy(() => import('./pages/AuditTrail').then(module => ({ default: module.AuditTrail })));
const Inventory = lazy(() => import('./pages/Inventory').then(module => ({ default: module.Inventory })));
const MaterialRequests = lazy(() => import('./pages/MaterialRequests').then(module => ({ default: module.MaterialRequests })));
const CPSEManagement = lazy(() => import('./pages/CPSEManagement').then(module => ({ default: module.CPSEManagement })));
const DataQuality = lazy(() => import('./pages/DataQuality').then(module => ({ default: module.DataQuality })));
const Integrations = lazy(() => import('./pages/Integrations').then(module => ({ default: module.Integrations })));
const ProcurementHistory = lazy(() => import('./pages/ProcurementHistory').then(module => ({ default: module.ProcurementHistory })));
const ProcurementOpportunities = lazy(() => import('./pages/ProcurementOpportunities').then(module => ({ default: module.ProcurementOpportunities })));
const NationalMaterial360 = lazy(() => import('./pages/NationalMaterial360').then(module => ({ default: module.NationalMaterial360 })));
const DuplicateClusters = lazy(() => import('./pages/DuplicateClusters').then(module => ({ default: module.DuplicateClusters })));
const ModelEvaluation = lazy(() => import('./pages/ModelEvaluation').then(module => ({ default: module.ModelEvaluation })));

const PageFallback = () => (
  <div className="min-h-[40vh] grid place-items-center text-slate-500 text-sm" role="status">
    Loading page...
  </div>
);

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, authReady } = useAuth();
  if (!authReady) return <div className="min-h-screen grid place-items-center bg-slate-950 text-slate-300 text-sm">Checking secure session...</div>;
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

const PermissionRoute = ({ permission, anyOf, children }) => {
  const { user } = useAuth();
  const allowed = permission
    ? hasPermission(user, permission)
    : (anyOf || []).some(item => hasPermission(user, item));
  return allowed ? children : <Navigate to="/dashboard" replace />;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, authReady } = useAuth();
  if (!authReady) return null;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}><Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<PermissionRoute permission="dashboard.read"><Dashboard /></PermissionRoute>} />
            <Route path="materials" element={<PermissionRoute permission="material.read"><Materials /></PermissionRoute>} />
            <Route path="import" element={<PermissionRoute permission="import.manage"><ImportMaterials /></PermissionRoute>} />
            <Route path="ai-recommendations" element={<PermissionRoute permission="matching.search"><AIRecommendations /></PermissionRoute>} />
            <Route path="duplicate-clusters" element={<PermissionRoute permission="approval.read"><DuplicateClusters /></PermissionRoute>} />
            <Route path="model-evaluation" element={<PermissionRoute permission="matching.search"><ModelEvaluation /></PermissionRoute>} />
            <Route path="comparison" element={<PermissionRoute permission="material.read"><MaterialComparison /></PermissionRoute>} />
            <Route path="national-materials" element={<PermissionRoute permission="national.read"><NationalMaterials /></PermissionRoute>} />
            <Route path="national-materials/:id" element={<PermissionRoute permission="national.read"><NationalMaterial360 /></PermissionRoute>} />
            <Route path="approvals" element={<PermissionRoute permission="approval.read"><Approvals /></PermissionRoute>} />
            <Route path="inventory" element={<PermissionRoute permission="inventory.read"><Inventory /></PermissionRoute>} />
            <Route path="procurement-history" element={<PermissionRoute permission="demand.read"><ProcurementHistory /></PermissionRoute>} />
            <Route path="procurement-opportunities" element={<PermissionRoute permission="demand.read"><ProcurementOpportunities /></PermissionRoute>} />
            <Route path="requests" element={<PermissionRoute anyOf={['request.read', 'request.read_all']}><MaterialRequests /></PermissionRoute>} />
            <Route path="cpses" element={<PermissionRoute permission="cpse.manage"><CPSEManagement /></PermissionRoute>} />
            <Route path="data-quality" element={<PermissionRoute permission="data_quality.read"><DataQuality /></PermissionRoute>} />
            <Route path="integrations" element={<PermissionRoute permission="integration.read"><Integrations /></PermissionRoute>} />
            <Route path="audit-trail" element={<PermissionRoute permission="audit.read"><AuditTrail /></PermissionRoute>} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes></Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
