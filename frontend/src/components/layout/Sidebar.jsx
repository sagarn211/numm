import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Package, 
  UploadCloud, 
  Sparkles, 
  GitCompare, 
  Globe2, 
  CheckSquare, 
  Activity,
  Layers,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Boxes,
  ClipboardList,
  Building2,
  ShieldCheck,
  PlugZap,
  TrendingUp,
  Network,
  FlaskConical
  ,Image
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../services/api';
import { hasPermission } from '../../utils/permissions';

export const Sidebar = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [pendingCount, setPendingCount] = React.useState(0);
  const [apiOnline, setApiOnline] = React.useState(true);
  const [aiOnline, setAiOnline] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  React.useEffect(() => {
    const fetchPending = async () => {
      if (!hasPermission(user, 'approval.read')) return;
      try {
        const res = await api.get('/api/clusters/approval-counts');
        setPendingCount(res.data?.actionable_total || 0);
      } catch {
        setPendingCount(0);
      }
    };
    fetchPending();
  }, [location.pathname, user]);

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, permission: 'dashboard.read' },
    { label: 'Materials Master', path: '/materials', icon: Package, permission: 'material.read' },
    { label: 'Import Data', path: '/import', icon: UploadCloud, permission: 'import.manage' },
    { label: 'AI Recommendations', path: '/ai-recommendations', icon: Sparkles, permission: 'matching.search' },
    { label: 'Duplicate Clusters', path: '/duplicate-clusters', icon: Network, permission: 'approval.read' },
    { label: 'Model Evaluation', path: '/model-evaluation', icon: FlaskConical, permission: 'matching.search' },
    { label: 'Material Comparison', path: '/comparison', icon: GitCompare, permission: 'material.read' },
    { label: 'Visual Material Search', path: '/visual-search', icon: Image, permission: 'material.read' },
    { label: 'National Materials', path: '/national-materials', icon: Globe2, permission: 'national.read' },
    { label: 'Approvals', path: '/approvals', icon: CheckSquare, permission: 'approval.read', badge: pendingCount > 0 ? String(pendingCount) : null },
    { label: 'Inventory', path: '/inventory', icon: Boxes, permission: 'inventory.read' },
    { label: 'Procurement History', path: '/procurement-history', icon: Boxes, permission: 'demand.read' },
    { label: 'Procurement Opportunities', path: '/procurement-opportunities', icon: TrendingUp, permission: 'demand.read' },
    { label: 'Material Requests', path: '/requests', icon: ClipboardList, anyOf: ['request.read', 'request.read_all'] },
    { label: 'CPSE Management', path: '/cpses', icon: Building2, permission: 'cpse.manage' },
    { label: 'Data Quality', path: '/data-quality', icon: ShieldCheck, permission: 'data_quality.read' },
    { label: 'Integrations', path: '/integrations', icon: PlugZap, permission: 'integration.read' },
    { label: 'Audit Trail', path: '/audit-trail', icon: Activity, permission: 'audit.read' },
  ].filter(item => item.permission
    ? hasPermission(user, item.permission)
    : item.anyOf?.some(permission => hasPermission(user, permission)));

  React.useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.get('/health');
        setApiOnline(res.status === 200);
      } catch {
        setApiOnline(false);
      }
      try {
        const aiRes = await api.get('/api/matching/health');
        setAiOnline(aiRes.data?.status !== 'offline');
      } catch {
        setAiOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside 
      className={`${collapsed ? 'w-20' : 'w-64'} bg-[#2A241F] text-[#eadcc9] flex flex-col h-screen sticky top-0 transition-all duration-300 z-40 border-r border-[#4b3a30] shadow-[0_12px_32px_rgba(32,22,18,0.18)]`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-[#4b3a30] bg-[#1F1A17]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#7d5a4a] via-[#a8775a] to-[#c69c6d] flex items-center justify-center text-white font-black text-lg shadow-md shrink-0 ring-1 ring-white/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col leading-tight">
              <span className="font-extrabold text-xs tracking-wider text-[#f8f2eb] uppercase">NATIONAL</span>
              <span className="font-bold text-[10px] text-[#d6b79f] tracking-widest uppercase">MATERIAL MASTER</span>
              <span className="text-[9px] text-[#d7c6b7] font-mono">GRID V2.4</span>
            </div>
          )}
        </div>
        <button 
          onClick={onToggle}
          className="p-1 rounded-md text-[#d4bda8] hover:bg-[#43362f] hover:text-[#fffaf4] transition-colors"
          title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Main Navigation Links */}
      <div className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        <div className={`px-3 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider ${collapsed ? 'text-center' : ''}`}>
          {collapsed ? 'NAV' : 'MAIN NAVIGATION'}
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path === '/dashboard' && location.pathname === '/');
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `
                relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-200 group
                ${isActive 
                  ? 'bg-[#8b634e]/18 text-[#fffaf4] border-l-4 border-[#d9b79a] pl-2.5 font-bold shadow-xs'
                  : 'text-[#d9c7b7] hover:bg-[#43362f]/70 hover:text-[#f8f2eb]'
                }
              `}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-[#e9c9a4]' : 'text-[#d9c7b7]'}`} />
              {!collapsed && (
                <span className="flex-1 truncate">{item.label}</span>
              )}
              {!collapsed && item.badge && (
                <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-[#d8a76c]/20 text-[#f2d1a2] border border-[#d8a76c]/40">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Bottom System Metrics */}
      <div className="p-3 border-t border-[#4b3a30] bg-[#1F1A17]">
        {!collapsed ? (
          <div className="space-y-2 mb-3">
            <div className="text-[10px] font-bold text-[#c6b7a8] uppercase tracking-wider">SYSTEM STATUS</div>
            <div className="space-y-1.5 text-[11px] bg-[#332c29] p-2.5 rounded-lg border border-[#4b3a30]">
              <div className="flex items-center justify-between">
                <span className="text-[#d9c7b7]">PostgreSQL / API</span>
                <span className={`flex items-center gap-1 font-semibold text-[10px] ${apiOnline ? 'text-[#a7d1a4]' : 'text-[#e8b1a5]'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${apiOnline ? 'bg-[#a7d1a4] animate-pulse' : 'bg-[#e8b1a5]'}`}></span>
                  {apiOnline ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#d9c7b7]">AI Service</span>
                <span className={`flex items-center gap-1 font-semibold text-[10px] ${aiOnline ? 'text-[#a7d1a4]' : 'text-[#e8b1a5]'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${aiOnline ? 'bg-[#a7d1a4] animate-pulse' : 'bg-[#e8b1a5]'}`}></span>
                  {aiOnline ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 mb-2">
            <span title={apiOnline ? "API Connected" : "API Disconnected"} className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-[#a7d1a4] animate-pulse' : 'bg-[#e8b1a5]'}`}></span>
            <span title={aiOnline ? "AI Engine Online" : "AI Engine Offline"} className={`w-2 h-2 rounded-full ${aiOnline ? 'bg-[#a7d1a4]' : 'bg-[#e8b1a5]'}`}></span>
          </div>
        )}

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-[#f5c8bc] hover:bg-[#a75d50]/12 hover:text-[#ffd6cc] transition-colors cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          {!collapsed && <span>Exit Session</span>}
        </button>
      </div>
    </aside>
  );
};
