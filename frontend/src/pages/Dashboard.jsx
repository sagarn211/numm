import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2, 
  Package, 
  Copy, 
  Sparkles, 
  Globe2, 
  Download,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Factory,
  Info
} from 'lucide-react';
import { dashboardApi } from '../services/dashboardApi';
import { StatCard } from '../components/dashboard/StatCard';
import { SectorCard } from '../components/dashboard/SectorCard';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { Loading } from '../components/common/Loading';
import { ProcurementPriceIntelligence } from '../components/dashboard/ProcurementPriceIntelligence';

export const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [sectors, setSectors] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, secRes, actRes] = await Promise.all([
          dashboardApi.getStats(),
          dashboardApi.getSectorStats(),
          dashboardApi.getRecentActivity()
        ]);
        setStats(statsRes.data);
        setSectors(secRes.data);
        setActivity(actRes.data);
      } catch (err) {
        console.error('Failed to load dashboard data', err);
        setError(err?.response?.data?.detail || err.message || 'Failed to load dashboard data from backend.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <Loading type="ai" text="Fetching National Material Master Live Intelligence..." />;
  }


  const totalMaterialsCount = stats?.totalMaterials?.value ?? 0;
  const mappedCount = stats?.aiMatches?.value ?? 0;
  const duplicateCount = stats?.duplicateMaterials?.value ?? 0;
  const pendingCount = stats?.pendingReviewCount ?? 0;
  const duplicateRisk = stats?.duplicateRiskPercent ?? 0;
  const harmonizationRate = totalMaterialsCount > 0
    ? Math.round((mappedCount / totalMaterialsCount) * 100)
    : 0;

  return (
    <div className="space-y-6 bg-micro-dot p-2 sm:p-4 rounded-2xl">
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-[#2f261f] tracking-tight">Material Intelligence</h2>
          <p className="text-sm text-[#6e625b] mt-1 font-medium">National Unified Material Master Live Overview</p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => window.print()}
            className="px-4 py-2 rounded-lg border border-[#d9cab7] bg-[#fffaf5] text-[#4c413b] font-semibold text-xs hover:bg-[#f3e9df] transition-colors flex items-center gap-2 shadow-[0_1px_0_rgba(59,44,35,0.05)] cursor-pointer"
          >
            <Download className="w-4 h-4 text-[#6c4738]" />
            Export Report
          </button>
          <button 
            onClick={() => navigate('/ai-recommendations')}
            className="px-4 py-2 rounded-lg bg-[#8b634e] text-white font-semibold text-xs hover:bg-[#6c4738] transition-colors flex items-center gap-2 shadow-[0_4px_12px_rgba(107,74,56,0.18)] cursor-pointer"
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
          value={String(stats?.totalCPSEs?.value ?? 0)}
          period="Participating CPSEs"
          icon={Building2}
          accentColor="blue"
        />
        <StatCard
          title="Total Materials"
          value={String(totalMaterialsCount)}
          period="Master items in DB"
          icon={Package}
          accentColor="cyan"
        />
        <StatCard
          title="Duplicates"
          value={String(duplicateCount)}
          period={`${duplicateRisk}% of materials at risk`}
          icon={Copy}
          accentColor="red"
          isRedAlert={duplicateCount > 0}
          statusBadge={{
            text: `${pendingCount} Pending review`,
            color: pendingCount > 0 ? 'text-rose-600' : 'text-slate-500',
            icon: AlertTriangle
          }}
        />
        <StatCard
          title="AI Matches"
          value={String(mappedCount)}
          period="Harmonized to National"
          icon={Sparkles}
          accentColor="indigo"
          isAiGlow={true}
          statusBadge={{ text: `${mappedCount} Mapped`, color: 'text-indigo-600', icon: CheckCircle2 }}
        />
        <StatCard
          title="National Codes"
          value={String(stats?.nationalMaterials?.value ?? 0)}
          period="Unified National Masters"
          icon={Globe2}
          accentColor="emerald"
          isGreenBorder={true}
          statusBadge={{ text: `${stats?.nationalMaterials?.value ?? 0} Standardized`, color: 'text-emerald-600', icon: CheckCircle2 }}
        />
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          ['Mapping coverage', `${stats?.mappingCoveragePercent ?? 0}%`],
          ['National harmonization index', `${stats?.harmonization?.index ?? 0}/100`],
          ['Verified procurement savings', 'Not yet measured'],
          ['Surplus by unit (current month)', (stats?.stockAnalytics?.by_unit || []).map(row => `${row.surplus} ${row.uom}`).join(' / ') || 'No stock'],
          ['Approval turnaround', `${stats?.approvalTurnaroundHours ?? 0} hours`],
        ].map(([label, value]) => <div key={label} className="rounded-xl border border-[#e7dccd] bg-[#fffaf5] p-4"><div className="text-[10px] font-bold uppercase tracking-wider text-[#7a6d63]">{label}</div><div className="mt-1 text-xl font-black text-[#2f261f]">{value}</div></div>)}
      </div>

      {/* Bento Grid Layout for Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-12 items-start gap-6">
        
        {/* Central Visualization: historical procurement intelligence (8 cols) */}
        <div className="xl:col-span-8 bg-[#fffaf5] border border-[#e7dccd] rounded-2xl p-6 relative overflow-hidden flex flex-col shadow-[0_1px_0_rgba(59,44,35,0.06)]">
          <ProcurementPriceIntelligence />
        </div>

        {/* Right Sidebar: AI Insights Engine & Recent Activity (4 cols) */}
        <div className="xl:col-span-4 flex flex-col gap-6">
          
          {/* AI Insights Card */}
          <div className="bg-[#fffaf5] border border-[#e7dccd] rounded-2xl p-6 ai-glow ai-border-gradient relative shadow-[0_1px_0_rgba(59,44,35,0.06)]">
            <div className="flex items-center gap-2.5 mb-4">
              <Cpu className="w-5 h-5 text-[#6c4738] animate-pulse" />
              <h3 className="text-base font-bold text-[#2f261f]">AI Intelligence Engine</h3>
            </div>
            
            <div className="mb-5">
              <div className="flex justify-between items-end mb-2">
                <span className="text-xs font-medium text-[#6e625b]">Harmonization Progress</span>
                <span className="text-lg font-black text-[#6c4738]">{harmonizationRate}%</span>
              </div>
              <div className="w-full bg-[#efe3d7] rounded-full h-2 overflow-hidden">
                <div className="bg-[#7d8f72] h-2 rounded-full transition-all duration-500" style={{ width: `${harmonizationRate}%` }}></div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="bg-[#f8e9e5] border border-[#ebcfc4] p-3 rounded-xl flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-[#a85d52] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#8f544e] block">Review Queue</span>
                  <span className="text-[12px] text-[#9d645d] font-medium leading-snug">
                    {pendingCount} candidate matches awaiting procurement officer authorization.
                  </span>
                </div>
              </div>

              <div className="bg-[#edf3ea] border border-[#d8e4d4] p-3 rounded-xl flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-[#637e59] shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-bold text-[#536d50] block">Unified National Master</span>
                  <span className="text-[12px] text-[#60775d] font-medium leading-snug">
                    {mappedCount} material records actively harmonized across participating CPSEs.
                  </span>
                </div>
              </div>
            </div>

            <button 
              onClick={() => navigate('/ai-recommendations')}
              className="w-full mt-4 py-2.5 border border-[#8b634e] text-[#6c4738] rounded-lg text-xs font-bold hover:bg-[#f3e9df] transition-colors cursor-pointer"
            >
              Review AI Recommendations
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

        {sectors.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {sectors.map((sec) => (
              <SectorCard key={sec.name} sector={sec} />
            ))}
          </div>
        ) : (
          <div className="bg-white border rounded-xl p-6 text-center text-xs text-slate-400">
            <Info className="w-5 h-5 mx-auto mb-1 opacity-50" />
            No sector data available.
          </div>
        )}
      </div>

    </div>
  );
};
