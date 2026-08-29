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
  FileText,
  Activity,
  Layers,
  ChevronLeft,
  ChevronRight,
  LogOut,
  ShieldAlert
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

import { nationalMaterialApi } from '../../services/nationalMaterialApi';

export const Sidebar = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [pendingCount, setPendingCount] = React.useState(2);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  React.useEffect(() => {
    const fetchPending = async () => {
      try {
        const res = await nationalMaterialApi.getApprovals();
        const pending = (res.data || []).filter(a => a.status === 'PENDING').length;
        setPendingCount(pending);
      } catch {
        setPendingCount(0);
      }
    };
    fetchPending();
  }, [location.pathname]);

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Materials Master', path: '/materials', icon: Package },
    { label: 'Import Data', path: '/import', icon: UploadCloud },
    { label: 'AI Recommendations', path: '/ai-recommendations', icon: Sparkles, badge: '94%' },
    { label: 'Material Comparison', path: '/comparison', icon: GitCompare },
    { label: 'National Materials', path: '/national-materials', icon: Globe2 },
    { label: 'Approvals', path: '/approvals', icon: CheckSquare, badge: pendingCount > 0 ? String(pendingCount) : null },
    { label: 'Audit Trail', path: '/audit-trail', icon: Activity },
  ];

  const [apiOnline, setApiOnline] = React.useState(true);

  React.useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) setApiOnline(true);
        else setApiOnline(false);
      } catch {
        setApiOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside 
      className={`${collapsed ? 'w-20' : 'w-64'} bg-[#0B1220] text-slate-300 flex flex-col h-screen sticky top-0 transition-all duration-300 z-40 border-r border-slate-800 shadow-xl`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80 bg-[#070C16]">
        <div className="flex items-center gap-3 overflow-hidden">
          {/* Abstract National Grid Logo */}
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-400 flex items-center justify-center text-white font-black text-lg shadow-md shrink-0 ring-1 ring-white/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col leading-tight">
              <span className="font-extrabold text-xs tracking-wider text-white uppercase">NATIONAL</span>
              <span className="font-bold text-[10px] text-blue-400 tracking-widest uppercase">MATERIAL MASTER</span>
              <span className="text-[9px] text-slate-400 font-mono">GRID V2.4</span>
            </div>
          )}
        </div>
        <button 
          onClick={onToggle}
          className="p-1 rounded-md text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
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
                  ? 'bg-blue-600/20 text-white border-l-4 border-blue-500 pl-2.5 font-bold shadow-xs' 
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }
              `}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
              {!collapsed && (
                <span className="flex-1 truncate">{item.label}</span>
              )}
              {!collapsed && item.badge && (
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                  item.badge === '94%' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Bottom System Metrics */}
      <div className="p-3 border-t border-slate-800/80 bg-[#070C16]">
        {!collapsed ? (
          <div className="space-y-2 mb-3">
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">SYSTEM STATUS</div>
            <div className="space-y-1.5 text-[11px] bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">API Status</span>
                <span className={`flex items-center gap-1 font-semibold text-[10px] ${apiOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${apiOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`}></span>
                  {apiOnline ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Data Pipeline</span>
                <span className="flex items-center gap-1 text-cyan-400 font-semibold text-[10px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span> Processing
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">AI Engine</span>
                <span className="flex items-center gap-1 text-emerald-400 font-semibold text-[10px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> Online
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 mb-2">
            <span title="API Connected" className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span title="Pipeline Processing" className="w-2 h-2 rounded-full bg-cyan-400"></span>
          </div>
        )}

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          {!collapsed && <span>Exit Session</span>}
        </button>
      </div>
    </aside>
  );
};
