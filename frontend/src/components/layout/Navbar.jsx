import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Bell, Sparkles, User, ShieldCheck, ChevronRight } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

export const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');

  // Compute title & breadcrumb based on route
  const getPageDetails = () => {
    switch (location.pathname) {
      case '/':
      case '/dashboard':
        return { title: 'Dashboard', breadcrumb: 'National Command Center' };
      case '/materials':
        return { title: 'Material Master', breadcrumb: 'CPSE Inventory' };
      case '/import':
        return { title: 'Import Materials', breadcrumb: 'Data Pipeline & Ingestion' };
      case '/ai-recommendations':
        return { title: 'AI Recommendations', breadcrumb: 'Decision Support & Clustering' };
      case '/comparison':
        return { title: 'Material Comparison', breadcrumb: 'Side-by-Side Parameter Workspace' };
      case '/national-materials':
        return { title: 'National Materials', breadcrumb: 'Unified Material Master Registry' };
      case '/approvals':
        return { title: 'Approvals', breadcrumb: 'Officer Governance & Review Queue' };
      case '/audit-trail':
        return { title: 'Audit Trail', breadcrumb: 'System Activity & Compliance History' };
      default:
        return { title: 'National Unified Material Master', breadcrumb: 'Grid' };
    }
  };

  const pageDetails = getPageDetails();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/materials?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      {/* Left: Breadcrumbs & Page Title */}
      <div className="flex items-center gap-3 min-w-[220px]">
        <div>
          <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            <span>NUMM</span>
            <ChevronRight className="w-3 h-3 text-slate-300" />
            <span className="text-blue-600">{pageDetails.breadcrumb}</span>
          </div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight leading-tight">{pageDetails.title}</h1>
        </div>
      </div>

      {/* Center: Global Material Search */}
      <div className="flex-1 max-w-xl mx-8 hidden md:block">
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search material code, description, specification..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-10 pr-4 py-2 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-2xs"
          />
          <kbd className="hidden sm:inline-block absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-400 font-mono shadow-2xs">
            ⌘K
          </kbd>
        </form>
      </div>

      {/* Right: AI Status & User Info */}
      <div className="flex items-center gap-4">
        {/* AI Engine Status Badge */}
        <div className="hidden lg:flex items-center gap-2 bg-gradient-to-r from-emerald-50 to-cyan-50 border border-emerald-200/80 px-3 py-1.5 rounded-full shadow-2xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <Sparkles className="w-3.5 h-3.5 text-cyan-600" />
          <span className="text-xs font-semibold text-slate-700">AI Engine Online</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-blue-600 rounded-full ring-2 ring-white"></span>
        </button>

        <div className="h-6 w-[1px] bg-slate-200 hidden sm:block"></div>

        {/* User Profile */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shadow-xs border border-slate-700">
            {user?.name ? user.name.split(' ').map(n => n[0]).join('') : 'RK'}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-bold text-slate-900 flex items-center gap-1">
              <span>{user?.name || 'Rajesh Kumar'}</span>
              <ShieldCheck className="w-3 h-3 text-blue-600" />
            </div>
            <div className="text-[10px] text-slate-500 font-medium">{user?.role || 'Procurement Officer'}</div>
          </div>
        </div>
      </div>
    </header>
  );
};
