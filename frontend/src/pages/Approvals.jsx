import React, { useEffect, useState } from 'react';
import { CheckSquare, CheckCircle2, XCircle, Sparkles, Eye, ShieldCheck, FileCheck } from 'lucide-react';
import { nationalMaterialApi } from '../services/nationalMaterialApi';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { getCPSEBadgeColor, formatConfidence } from '../utils/formatters';

export const Approvals = () => {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('PENDING'); // PENDING | APPROVED | REJECTED
  const [selectedApproval, setSelectedApproval] = useState(null);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const res = await nationalMaterialApi.getApprovals();
      setApprovals(res.data);
    } catch (err) {
      console.error('Failed to load approvals', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleApprove = async (id) => {
    await nationalMaterialApi.approveMapping(id);
    setSelectedApproval(null);
    loadApprovals();
  };

  const handleReject = async (id) => {
    await nationalMaterialApi.rejectMapping(id, 'Officer rejected candidate pair');
    setSelectedApproval(null);
    loadApprovals();
  };

  const filteredApprovals = approvals.filter(a => a.status === tab);

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Procurement Officer Approval Center</h2>
          <p className="text-xs text-slate-500 mt-0.5">Governance queue for evaluating and authorizing AI candidate national mappings</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white p-2 rounded-xl border border-slate-200/80 shadow-2xs flex items-center gap-2 text-xs font-bold">
        <button
          onClick={() => setTab('PENDING')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            tab === 'PENDING' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>Pending Review Queue</span>
          <span className="bg-blue-800 text-white px-2 py-0.5 rounded-full text-[10px] font-mono">
            {approvals.filter(a => a.status === 'PENDING').length}
          </span>
        </button>
        <button
          onClick={() => setTab('APPROVED')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            tab === 'APPROVED' ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>Approved Mappings</span>
          <span className="bg-emerald-800 text-white px-2 py-0.5 rounded-full text-[10px] font-mono">
            {approvals.filter(a => a.status === 'APPROVED').length}
          </span>
        </button>
        <button
          onClick={() => setTab('REJECTED')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            tab === 'REJECTED' ? 'bg-rose-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>Rejected Items</span>
          <span className="bg-rose-800 text-white px-2 py-0.5 rounded-full text-[10px] font-mono">
            {approvals.filter(a => a.status === 'REJECTED').length}
          </span>
        </button>
      </div>

      {/* List */}
      {loading ? (
        <Loading type="skeleton" rows={4} />
      ) : filteredApprovals.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title={`No ${tab} Approvals`}
          description="There are no items currently in this review queue."
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden shadow-2xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Material Group</th>
                  <th className="py-3 px-4">Participating CPSEs</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">AI Confidence</th>
                  <th className="py-3 px-4">Recommendation</th>
                  <th className="py-3 px-4">Submitted</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
                {filteredApprovals.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50">
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {app.materialGroup}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex gap-1">
                        {app.cpses.map((c, i) => (
                          <span key={i} className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${getCPSEBadgeColor(c)}`}>
                            {c}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">{app.category}</td>
                    <td className="py-3.5 px-4 font-mono font-bold text-emerald-600">
                      {formatConfidence(app.aiConfidence)}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-blue-600">
                      {app.recommendation}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 font-mono">{app.submittedDate}</td>
                    <td className="py-3.5 px-4 text-right">
                      <Button variant="primary" size="sm" icon={Eye} onClick={() => setSelectedApproval(app)}>
                        Review & Approve
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Side-by-Side Review & Approval Workspace Modal */}
      <Modal
        open={!!selectedApproval}
        onClose={() => setSelectedApproval(null)}
        title="Officer Approval Workspace"
        subtitle={`Reviewing candidate mapping for ${selectedApproval?.materialGroup}`}
        maxWidth="max-w-3xl"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setSelectedApproval(null)}>
              Close
            </Button>
            <Button variant="danger" size="sm" icon={XCircle} onClick={() => handleReject(selectedApproval?.id)}>
              Reject Mapping
            </Button>
            <Button variant="success" size="sm" icon={CheckCircle2} onClick={() => handleApprove(selectedApproval?.id)}>
              Approve Mapping
            </Button>
          </div>
        }
      >
        {selectedApproval && (
          <div className="space-y-5 text-xs">
            {/* Recommendation Banner */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-[10px] font-bold text-blue-800 uppercase font-mono">AI RECOMMENDATION EVIDENCE</span>
                <h4 className="text-sm font-bold text-slate-900 mt-0.5">{selectedApproval.recommendation}</h4>
                <p className="text-slate-600 text-xs mt-1">Overall AI Confidence: <strong className="text-emerald-700">{formatConfidence(selectedApproval.aiConfidence)}</strong></p>
              </div>
            </div>

            {/* Evidence Checklist */}
            <div>
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                Automated Evidence Audit Checks
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {selectedApproval.evidence?.map((ev, idx) => (
                  <div key={idx} className="p-2.5 bg-emerald-50 text-emerald-900 border border-emerald-200 rounded-lg font-medium flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{ev}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CPSE Original Codes */}
            <div>
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                CPSE Source Codes Included in Candidate
              </h4>
              <div className="space-y-2 font-mono">
                {selectedApproval.originalCodes?.map((code, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getCPSEBadgeColor(selectedApproval.cpses[idx] || 'CPSE')}`}>
                        {selectedApproval.cpses[idx] || 'CPSE'}
                      </span>
                      <span className="font-bold text-slate-900">{code}</span>
                    </div>
                    <span className="text-slate-500 font-sans">Industrial Spec Verified</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Compliance Warning */}
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-[11px] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Officer approval is legally binding and registers this candidate directly to the National Material Master Registry.</span>
            </div>
          </div>
        )}
      </Modal>

    </div>
  );
};
