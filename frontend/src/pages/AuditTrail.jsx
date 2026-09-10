import { useCallback, useEffect, useState } from 'react';
import { Activity, Search, User, Clock, ShieldCheck, ShieldAlert } from 'lucide-react';
import { nationalMaterialApi } from '../services/nationalMaterialApi';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { getCPSEBadgeColor } from '../utils/formatters';

export const AuditTrail = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cpseFilter, setCpseFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [integrity, setIntegrity] = useState(null);
  const [error, setError] = useState('');

  const loadAuditLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [res, verification] = await Promise.all([
        nationalMaterialApi.getAuditTrail({ cpse: cpseFilter, search }),
        nationalMaterialApi.verifyAuditTrail(),
      ]);
      setLogs(res.data);
      setIntegrity(verification.data);
    } catch (err) {
      setLogs([]);
      setIntegrity(null);
      setError(err?.response?.data?.detail || err.message || 'Failed to load the governance ledger.');
    } finally {
      setLoading(false);
    }
  }, [cpseFilter, search]);

  useEffect(() => {
    loadAuditLogs();
  }, [loadAuditLogs]);

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Audit & Governance Trail</h2>
          <p className="text-xs text-slate-500 mt-0.5">Immutable record of all system events, data ingestions, AI recommendations, and officer approval actions</p>
        </div>
      </div>

      {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">{error}</div>}
      {integrity && <div className={`flex items-center gap-3 rounded-xl border p-4 ${integrity.status === 'VALID' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-rose-200 bg-rose-50 text-rose-800'}`}>
        {integrity.status === 'VALID' ? <ShieldCheck className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
        <div>
          <div className="text-xs font-bold">Tamper-Evident Governance Ledger: {integrity.status}</div>
          <div className="text-[11px]">{integrity.hashed_records_checked} hashed events verified; {integrity.legacy_unhashed_records} legacy events remain outside the cryptographic boundary.</div>
        </div>
      </div>}

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter audit log by user name, material code, or action details..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <select
            value={cpseFilter}
            onChange={(e) => setCpseFilter(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All CPSE Enterprises</option>
            <option value="ONGC">ONGC</option>
            <option value="NTPC">NTPC</option>
            <option value="SAIL">SAIL</option>
            <option value="CIL">CIL</option>
            <option value="BHEL">BHEL</option>
            <option value="NATIONAL">NATIONAL</option>
            <option value="SYSTEM">SYSTEM (AI)</option>
          </select>
        </div>
      </div>

      {/* Timeline List */}
      {loading ? (
        <Loading type="skeleton" rows={5} />
      ) : logs.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No Audit Events Found"
          description="No governance activity matches your filter criteria."
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-2xs">
          <div className="relative border-l-2 border-slate-200 ml-4 space-y-6">
            {logs.map((log) => {
              const badgeClass = getCPSEBadgeColor(log.cpse);

              return (
                <div key={log.id} className="relative pl-6 group">
                  {/* Timeline Dot */}
                  <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-4 border-blue-600 group-hover:border-cyan-500 transition-colors"></div>

                  <div className="bg-slate-50/80 border border-slate-200/80 rounded-xl p-4 space-y-2 hover:bg-white hover:shadow-xs transition-all">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${badgeClass}`}>
                          {log.cpse}
                        </span>
                        <span className="text-xs font-bold text-slate-900">{log.action}</span>
                      </div>
                      <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" /> {log.timestamp}
                      </span>
                    </div>

                    <p className="text-xs font-medium text-slate-800">{log.details}</p>

                    <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-200/60 font-mono">
                      <span className="flex items-center gap-1 text-slate-700 font-sans font-semibold">
                        <User className="w-3 h-3 text-blue-600" /> {log.user}
                      </span>
                      <span>Target: {log.materialCode}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

    </div>
  );
};
