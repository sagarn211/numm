import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Bell, Sparkles, ShieldCheck, ChevronRight } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { api } from '../../services/api';
import { roleLabel } from '../../utils/permissions';

export const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [aiOnline, setAiOnline] = useState(false);
  const [aiEngine, setAiEngine] = useState(null);

  useEffect(() => {
    const checkAi = async () => {
      try {
        const res = await api.get('/api/matching/health');
        setAiOnline(res.data?.status !== 'offline');
        setAiEngine(res.data?.engine || null);
      } catch {
        setAiOnline(false);
        setAiEngine(null);
      }
    };
    checkAi();
    const interval = setInterval(checkAi, 30000);
    return () => clearInterval(interval);
  }, []);

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
      case '/inventory': return { title: 'Cross-CPSE Inventory', breadcrumb: 'Reuse Before Procurement' };
      case '/requests': return { title: 'Material Requests', breadcrumb: 'Reservation & Allocation' };
      case '/cpses': return { title: 'CPSE Management', breadcrumb: 'Participating Enterprises' };
      case '/data-quality': return { title: 'Data Quality', breadcrumb: 'Master Data Governance' };
      case '/integrations': return { title: 'Integrations', breadcrumb: 'ERP / SAP Connectivity' };
      case '/audit-trail':
        return { title: 'Audit Trail', breadcrumb: 'System Activity & Compliance History' };
      default:
        return { title: 'National Unified Material Master', breadcrumb: 'Grid' };
    }
  };

  const pageDetails = getPageDetails();
  const fallbackActive = aiOnline && aiEngine === 'FALLBACK';

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/materials?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="h-16 bg-[#f8f3ee] border-b border-[#e3d2bb] px-6 flex items-center justify-between sticky top-0 z-30 shadow-[0_1px_0_rgba(91,73,57,0.08)]">
      {/* Left: Breadcrumbs & Page Title */}
      <div className="flex items-center gap-3 min-w-[220px]">
        <div>
          <div className="flex items-center gap-1 text-[11px] font-semibold text-[#7a6d63] uppercase tracking-wider">
            <span>NUMM</span>
            <ChevronRight className="w-3 h-3 text-[#b3a294]" />
            <span className="text-[#6c4738]">{pageDetails.breadcrumb}</span>
          </div>
          <h1 className="text-lg font-bold text-[#2f261f] tracking-tight leading-tight">{pageDetails.title}</h1>
        </div>
      </div>

      {/* Center: Global Material Search */}
      <div className="flex-1 max-w-xl mx-8 hidden md:block">
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="w-4 h-4 text-[#847569] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search material code, description, specification..."
            className="w-full bg-[#f3ece4] border border-[#dcc9b8] rounded-lg pl-10 pr-4 py-2 text-xs font-medium text-[#2f261f] placeholder-[#8a7f76] focus:outline-none focus:ring-2 focus:ring-[#8b634e] focus:bg-[#fffaf5] transition-all shadow-[0_1px_0_rgba(59,44,35,0.05)]"
          />
          <kbd className="hidden sm:inline-block absolute right-3 top-1/2 -translate-y-1/2 text-[10px] bg-white border border-[#e1d5c7] px-1.5 py-0.5 rounded text-[#7a6d63] font-mono shadow-[0_1px_0_rgba(59,44,35,0.05)]">
            Enter
          </kbd>
        </form>
      </div>

      {/* Right: AI Status & User Info */}
      <div className="flex items-center gap-4">
        {/* AI Engine Status Badge */}
        <div className={`hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full shadow-[0_1px_0_rgba(59,44,35,0.05)] border ${
          aiOnline
            ? 'bg-[#edf5ee] border-[#b9d2bb]'
            : 'bg-[#f6e9e5] border-[#ebc5bd] text-[#8f544e]'
        }`}>
          <span className="relative flex h-2 w-2">
            {aiOnline && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#7d8f72] opacity-75"></span>}
            <span className={`relative inline-flex rounded-full h-2 w-2 ${aiOnline ? (fallbackActive ? 'bg-amber-500' : 'bg-[#6b8d63]') : 'bg-[#b75d50]'}`}></span>
          </span>
          <Sparkles className={`w-3.5 h-3.5 ${aiOnline ? 'text-[#5f7158]' : 'text-[#b75d50]'}`} />
          <span className="text-xs font-semibold text-[#4b403c]">
            {aiOnline ? (fallbackActive ? 'Fallback Matcher Active' : 'AI Service Online') : 'AI Service Offline'}
          </span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 text-[#70635d] hover:text-[#2f261f] hover:bg-[#efe4d8] rounded-lg transition-colors">
          <Bell className="w-4 h-4" />
        </button>

        <div className="h-6 w-[1px] bg-[#dcc9b8] hidden sm:block"></div>

        {/* User Profile */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#2a241f] text-[#fffaf5] flex items-center justify-center font-bold text-xs shadow-xs border border-[#4d4039]">
            {user?.name ? user.name.split(' ').map(n => n[0]).join('') : 'U'}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-bold text-[#2f261f] flex items-center gap-1">
              <span>{user?.name || 'Authenticated User'}</span>
              <ShieldCheck className="w-3 h-3 text-[#6c4738]" />
            </div>
            <div className="text-[10px] text-[#756b62] font-medium">{roleLabel(user?.role)}</div>
          </div>
        </div>
      </div>
    </header>
  );
};
