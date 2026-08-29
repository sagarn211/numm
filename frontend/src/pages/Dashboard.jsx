import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, 
  Package, 
  Copy, 
  Sparkles, 
  Globe2, 
  Download,
  Network,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Award,
  Factory,
  Cog
} from 'lucide-react';
import { dashboardApi } from '../services/dashboardApi';
import { StatCard } from '../components/dashboard/StatCard';
import { SectorCard } from '../components/dashboard/SectorCard';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { Loading } from '../components/common/Loading';

export const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [networkData, setNetworkData] = useState(null);
  const [sectors, setSectors] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNodeIndex, setSelectedNodeIndex] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, netRes, secRes, actRes] = await Promise.all([
          dashboardApi.getStats(),
          dashboardApi.getMaterialNetwork(),
          dashboardApi.getSectorStats(),
          dashboardApi.getRecentActivity()
        ]);
        setStats(statsRes.data);
        setNetworkData(netRes.data);
        setSectors(secRes.data);
        setActivity(actRes.data);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <Loading type="ai" text="Initializing National Material Intelligence Grid..." />;
  }

  // Active convergence node details
  const activeNode = networkData?.nationalNodes?.[selectedNodeIndex] || {
    id: 'NM-VAL-001',
    title: 'Standardized Gate Valve, 150mm',
    cpses: [
      { cpse: 'ONGC', code: 'ONG-V-1029' },
      { cpse: 'NTPC', code: 'NTP-VAL-44' },
      { cpse: 'SAIL', code: 'SL-V-002' },
      { cpse: 'BHEL', code: 'BH-VL-991' }
    ]
  };

  return (
    <div className="space-y-6 bg-micro-dot p-2 sm:p-4 rounded-2xl">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Material Intelligence</h2>
          <p className="text-sm text-slate-500 mt-1 font-medium">National Unified Material Master Overview</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => window.print()}
            className="px-4 py-2 rounded-lg border border-slate-300 bg-white text-slate-700 font-semibold text-xs hover:bg-slate-50 transition-colors flex items-center gap-2 shadow-2xs cursor-pointer"
          >
            <Download className="w-4 h-4 text-slate-500" />
            Export Report
          </button>
          <button 
            onClick={() => navigate('/ai-recommendations')}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold text-xs hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-sm cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            Run AI Analysis
          </button>
        </div>
      </div>

      {/* Top 5 Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Total CPSEs"
          value={stats?.totalCPSEs?.value || '14'}
          change="+2"
          period="this quarter"
          icon={Building2}
          accentColor="blue"
        />
        <StatCard
          title="Total Materials"
          value={stats?.totalMaterials?.value ? `${(stats.totalMaterials.value / 1000000).toFixed(1)}M` : '2.4M'}
          period="Synced 2h ago"
          icon={Package}
          accentColor="cyan"
        />
        <StatCard
          title="Duplicates"
          value={stats?.duplicateMaterials?.value ? `${(stats.duplicateMaterials.value / 1000).toFixed(0)}k` : '342k'}
          period="Pending review"
          icon={Copy}
          accentColor="red"
          isRedAlert={true}
          statusBadge={{ text: 'Pending review', color: 'text-rose-600', icon: AlertTriangle }}
        />
        <StatCard
          title="AI Matches"
          value={stats?.aiMatches?.value ? `${(stats.aiMatches.value / 1000).toFixed(0)}k` : '894k'}
          period="92% Confidence Avg"
          icon={Sparkles}
          accentColor="indigo"
          isAiGlow={true}
          statusBadge={{ text: '92% Confidence Avg', color: 'text-indigo-600', icon: CheckCircle2 }}
        />
        <StatCard
          title="National Codes"
          value={stats?.nationalMaterials?.value ? `${(stats.nationalMaterials.value / 1000000).toFixed(1)}M` : '1.2M'}
          period="Standardized"
          icon={Globe2}
          accentColor="emerald"
          isGreenBorder={true}
          statusBadge={{ text: 'Standardized', color: 'text-emerald-600', icon: CheckCircle2 }}
        />
      </div>

      {/* Bento Grid Layout for Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        
        {/* Central Visualization: Material Network Convergence (8 cols) */}
        <div className="xl:col-span-8 bg-white border border-slate-200/80 rounded-2xl p-6 relative overflow-hidden flex flex-col shadow-2xs">
          <div className="flex justify-between items-center mb-6 z-10">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Network className="w-5 h-5 text-blue-600" />
              Material Network Convergence
            </h3>
            <div className="flex gap-2">
              <span className="bg-slate-100 px-3 py-1 rounded-full text-xs font-semibold text-slate-600">
                Live Map
              </span>
            </div>
          </div>

          {/* Network Viz Canvas */}
          <div className="flex-1 min-h-[400px] relative rounded-xl border border-slate-200/60 bg-slate-50/70 flex items-center justify-center p-6 sm:p-8">
            {/* Connecting SVG Lines */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
              <path className="network-line" d="M 100,80 C 220,80 220,200 400,200" fill="none" opacity="0.6" stroke="#94a3b8" strokeWidth="1.5"></path>
              <path className="network-line" d="M 100,160 C 220,160 220,200 400,200" fill="none" opacity="0.6" stroke="#94a3b8" strokeWidth="1.5"></path>
              <path className="network-line" d="M 100,240 C 220,240 220,200 400,200" fill="none" opacity="0.6" stroke="#94a3b8" strokeWidth="1.5"></path>
              <path className="network-line" d="M 100,320 C 220,320 220,200 400,200" fill="none" opacity="0.6" stroke="#94a3b8" strokeWidth="1.5"></path>
              {/* Convergence line to final node */}
              <path className="network-line" d="M 400,200 L 560,200" fill="none" stroke="#4f46e5" strokeDasharray="5,5" strokeWidth="2"></path>
            </svg>

            <div className="w-full flex flex-col md:flex-row justify-between items-center gap-6 relative z-10">
              
              {/* Left: CPSE Nodes */}
              <div className="flex flex-col gap-4 w-full md:w-1/4">
                {(activeNode.cpses || [
                  { cpse: 'ONGC', code: 'ONG-V-1029' },
                  { cpse: 'NTPC', code: 'NTP-VAL-44' },
                  { cpse: 'SAIL', code: 'SL-V-002' },
                  { cpse: 'BHEL', code: 'BH-VL-991' }
                ]).map((item, idx) => (
                  <div 
                    key={idx}
                    className="bg-white border border-slate-200 p-3 rounded-lg shadow-2xs text-center transform transition hover:scale-105 hover:border-blue-500 hover:shadow-md cursor-pointer"
                  >
                    <span className="text-xs font-bold text-slate-900 block">{item.cpse}</span>
                    <p className="font-mono text-[10px] text-slate-500 mt-0.5">{item.code || item.title}</p>
                  </div>
                ))}
              </div>

              {/* Middle: Material Group Node */}
              <div className="w-full md:w-1/3 flex justify-center">
                <div className="bg-slate-100 border border-slate-300 p-5 rounded-2xl shadow-2xs text-center relative w-full max-w-[220px]">
                  <div className="absolute -top-3 -right-2 bg-indigo-100 text-indigo-700 text-[10px] font-bold px-2 py-0.5 rounded-full border border-indigo-200 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> 98% Match
                  </div>
                  <Cog className="w-8 h-8 text-slate-400 mx-auto mb-1 animate-spin-slow" />
                  <span className="block text-xs font-bold text-slate-900">Gate Valve Group X</span>
                  <p className="font-mono text-[11px] text-slate-500 mt-1">4 Entities Detected</p>
                </div>
              </div>

              {/* Right: National Code Node */}
              <div className="w-full md:w-1/3 flex justify-end">
                <div className="bg-white border-2 border-emerald-500 p-5 rounded-2xl shadow-lg text-center relative overflow-hidden group hover:border-emerald-600 transition-all cursor-pointer w-full max-w-[260px]">
                  <div className="absolute inset-0 bg-emerald-50/50 group-hover:opacity-100 transition-opacity"></div>
                  <div className="relative z-10">
                    <div className="bg-emerald-100 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-2 shadow-2xs">
                      <Award className="w-6 h-6 text-emerald-700" />
                    </div>
                    <span className="block text-[10px] font-bold text-emerald-700 tracking-widest uppercase mb-0.5">National Code</span>
                    <span className="block font-mono text-xl font-black text-slate-900">{activeNode.id}</span>
                    <p className="text-xs font-medium text-slate-600 mt-2 leading-tight">
                      {activeNode.title || activeNode.standardDescription}
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* Right Sidebar: AI Insights Engine & Recent Activity (4 cols) */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          
          {/* AI Insights Card */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 ai-glow ai-border-gradient relative shadow-2xs">
            <div className="flex items-center gap-2.5 mb-4">
              <Cpu className="w-5 h-5 text-indigo-600 animate-pulse" />
              <h3 className="text-base font-bold text-slate-900">AI Insights Engine</h3>
            </div>
            
            <div className="mb-5">
              <div className="flex justify-between items-end mb-2">
                <span className="text-xs font-medium text-slate-500">Global Matching Confidence</span>
                <span className="text-lg font-black text-indigo-600">94.7%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div className="bg-indigo-600 h-2 rounded-full transition-all duration-500" style={{ width: '94.7%' }}></div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="bg-rose-50 border border-rose-100 p-3 rounded-xl flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-rose-700 block">Duplicates Detected</span>
                  <span className="text-[12px] text-rose-600 font-medium leading-snug">
                    1,284 potential duplicates found in recent batch upload from Coal Sector.
                  </span>
                </div>
              </div>

              <div className="bg-emerald-50 border border-emerald-100 p-3 rounded-xl flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-emerald-700 block">Auto-Mapping Success</span>
                  <span className="text-[12px] text-emerald-600 font-medium leading-snug">
                    850 materials automatically mapped to National Codes with &gt;95% confidence.
                  </span>
                </div>
              </div>
            </div>

            <button 
              onClick={() => navigate('/ai-recommendations')}
              className="w-full mt-4 py-2.5 border border-indigo-600 text-indigo-600 rounded-lg text-xs font-bold hover:bg-indigo-50 transition-colors cursor-pointer"
            >
              Review AI Flags
            </button>
          </div>

          {/* System Activity Timeline */}
          <RecentActivity activities={activity} />

        </div>

      </div>

      {/* Bottom Row: Sector Progress */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Factory className="w-4 h-4 text-slate-400" />
            CPSE Sector Harmonization Progress
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {(sectors.length > 0 ? sectors.slice(0, 3) : [
            { name: 'Steel Sector', materials: 450000, standardization: 82, cpseList: ['SAIL', 'RINL'] },
            { name: 'Power Sector', materials: 780000, standardization: 64, cpseList: ['NTPC', 'PGCIL'] },
            { name: 'Oil & Gas', materials: 1100000, standardization: 41, cpseList: ['ONGC', 'IOCL'] }
          ]).map((sec) => (
            <SectorCard key={sec.name} sector={sec} />
          ))}
        </div>
      </div>

    </div>
  );
};

