import { useCallback, useEffect, useState } from 'react';
import { CheckSquare, CheckCircle2, XCircle, Sparkles, Eye, ShieldCheck } from 'lucide-react';
import { nationalMaterialApi } from '../services/nationalMaterialApi';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { getCPSEBadgeColor, formatConfidence } from '../utils/formatters';
import { useAuth } from '../hooks/useAuth';
import { hasPermission } from '../utils/permissions';

const PAGE_SIZE = 25;

export const Approvals = () => {
  const { user } = useAuth();
  const canReview = hasPermission(user, 'approval.review');
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('PENDING'); // PENDING | APPROVED | REJECTED
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({ page: 1, limit: PAGE_SIZE, total: 0, pages: 0 });
  const [counts, setCounts] = useState({ PENDING: 0, APPROVED: 0, REJECTED: 0 });
  const [classification, setClassification] = useState('ALL');
  const [sortBy, setSortBy] = useState('CONFIDENCE_DESC');
  const [classificationCounts, setClassificationCounts] = useState({ EXACT: 0, NEAR_DUPLICATE: 0, FUNCTIONAL_EQUIVALENT: 0 });
  const [canonicalValues, setCanonicalValues] = useState({});
  const [functionalEquivalentAcknowledged, setFunctionalEquivalentAcknowledged] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [substitutionConditions, setSubstitutionConditions] = useState('');

  const loadApprovals = useCallback(async (requestedPage = page) => {
    setLoading(true);
    try {
      const res = await nationalMaterialApi.getApprovals(tab, requestedPage, PAGE_SIZE, { classification, sortBy });
      setApprovals(res.data || []);
      setPagination(res.pagination || { page: requestedPage, limit: PAGE_SIZE, total: 0, pages: 0 });
      setCounts(res.counts || { PENDING: 0, APPROVED: 0, REJECTED: 0 });
      setClassificationCounts(res.classificationCounts || { EXACT: 0, NEAR_DUPLICATE: 0, FUNCTIONAL_EQUIVALENT: 0 });
    } catch (err) {
      console.error('Failed to load approvals', err);
    } finally {
      setLoading(false);
    }
  }, [classification, page, sortBy, tab]);

  useEffect(() => {
    // Approval data is loaded when the selected server-side page changes.
    loadApprovals();
  }, [loadApprovals]);

  const selectTab = (nextTab) => {
    setTab(nextTab);
    setPage(1);
    setSelectedApproval(null);
  };

  const handleApprove = async (id) => {
    const critical = (selectedApproval?.conflicts || []).filter(item => item.requires_review);
    const unresolved = critical.filter(item => !canonicalValues[item.field]);
    if (unresolved.length && selectedApproval?.classification !== 'FUNCTIONAL_EQUIVALENT') {
      setReviewError('Resolve every safety-critical conflict before approval.');
      return;
    }
    const isFunctionalEquivalent = selectedApproval?.classification === 'FUNCTIONAL_EQUIVALENT';
    if (isFunctionalEquivalent && !functionalEquivalentAcknowledged) {
      setReviewError('Explicitly acknowledge the functional-equivalent mapping policy before approval.');
      return;
    }
    if (isFunctionalEquivalent && !substitutionConditions.trim()) {
      setReviewError('Describe the intended application and substitution limitations.');
      return;
    }
    try {
      await nationalMaterialApi.approveMapping(id, isFunctionalEquivalent ? substitutionConditions : 'Officer approved canonical values', canonicalValues, critical.length > 0, functionalEquivalentAcknowledged);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setReviewError(typeof detail === 'string' ? detail : detail?.message || err.message || 'Unable to approve this mapping.');
      return;
    }
    setSelectedApproval(null);
    const nextPage = approvals.length === 1 && page > 1 ? page - 1 : page;
    if (nextPage !== page) setPage(nextPage);
    else loadApprovals(nextPage);
  };

  const handleReject = async (id) => {
    try {
      await nationalMaterialApi.rejectMapping(id, 'Officer rejected candidate pair');
    } catch (err) {
      setReviewError(err?.response?.data?.detail || err.message || 'Unable to reject this mapping.');
      return;
    }
    setSelectedApproval(null);
    const nextPage = approvals.length === 1 && page > 1 ? page - 1 : page;
    if (nextPage !== page) setPage(nextPage);
    else loadApprovals(nextPage);
  };

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
          onClick={() => selectTab('PENDING')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            tab === 'PENDING' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>Pending Review Queue</span>
          <span className="bg-blue-800 text-white px-2 py-0.5 rounded-full text-[10px] font-mono">
            {counts.PENDING}
          </span>
        </button>
        <button
          onClick={() => selectTab('APPROVED')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            tab === 'APPROVED' ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>Approved Mappings</span>
          <span className="bg-emerald-800 text-white px-2 py-0.5 rounded-full text-[10px] font-mono">
            {counts.APPROVED}
          </span>
        </button>
        <button
          onClick={() => selectTab('REJECTED')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
            tab === 'REJECTED' ? 'bg-rose-600 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>Rejected Items</span>
          <span className="bg-rose-800 text-white px-2 py-0.5 rounded-full text-[10px] font-mono">
            {counts.REJECTED}
          </span>
        </button>
      </div>

      {/* Duplicate filters */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200/80 bg-white p-3 shadow-2xs sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-bold text-slate-600">Duplicate type</span>
          <select
            value={classification}
            onChange={(event) => { setClassification(event.target.value); setPage(1); }}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 font-semibold text-slate-700"
          >
            <option value="ALL">All candidates ({Object.values(classificationCounts).reduce((sum, count) => sum + count, 0)})</option>
            <option value="EXACT">Exact duplicates ({classificationCounts.EXACT})</option>
            <option value="NEAR_DUPLICATE">Near duplicates ({classificationCounts.NEAR_DUPLICATE})</option>
            <option value="FUNCTIONAL_EQUIVALENT">Functional equivalents ({classificationCounts.FUNCTIONAL_EQUIVALENT})</option>
          </select>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="approval-sort" className="font-bold text-slate-600">Sort</label>
          <select
            id="approval-sort"
            value={sortBy}
            onChange={(event) => { setSortBy(event.target.value); setPage(1); }}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 font-semibold text-slate-700"
          >
            <option value="CONFIDENCE_DESC">Highest confidence first</option>
            <option value="CONFIDENCE_ASC">Lowest confidence first</option>
            <option value="NEWEST">Newest first</option>
            <option value="OLDEST">Oldest first</option>
          </select>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <Loading type="skeleton" rows={4} />
      ) : approvals.length === 0 ? (
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
                {approvals.map((app) => (
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
                      <Button variant="primary" size="sm" icon={Eye} onClick={() => { setSelectedApproval(app); setCanonicalValues({}); setFunctionalEquivalentAcknowledged(false); setSubstitutionConditions(''); setReviewError(''); }}>
                        {tab === 'PENDING' && canReview ? 'Review & Approve' : 'View Details'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {pagination.pages > 1 && (
            <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-200 p-3 sm:flex-row">
              <span className="text-xs text-slate-500">
                Showing {(pagination.page - 1) * pagination.limit + 1}–{Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total}
              </span>
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage(current => current - 1)}>
                  Previous
                </Button>
                <span className="min-w-24 text-center text-xs font-semibold text-slate-700">
                  Page {pagination.page} of {pagination.pages}
                </span>
                <Button variant="secondary" size="sm" disabled={page >= pagination.pages} onClick={() => setPage(current => current + 1)}>
                  Next
                </Button>
              </div>
            </div>
          )}
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
            {tab === 'PENDING' && canReview && (
              <>
                <Button variant="danger" size="sm" icon={XCircle} onClick={() => handleReject(selectedApproval?.id)}>
                  Reject Mapping
                </Button>
                <Button variant="success" size="sm" icon={CheckCircle2} onClick={() => handleApprove(selectedApproval?.id)}>
                  {selectedApproval?.classification === 'FUNCTIONAL_EQUIVALENT' ? 'Approve Substitution Recommendation' : 'Approve Mapping'}
                </Button>
              </>
            )}
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
            {(selectedApproval.conflicts || []).length > 0 && <div className="space-y-2">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">Canonical conflict resolution</h4>
              {selectedApproval.conflicts.map(conflict => <label key={conflict.field} className={`block rounded-lg border p-3 ${conflict.requires_review ? 'border-rose-300 bg-rose-50' : 'border-amber-200 bg-amber-50'}`}>
                <span className="mb-2 block font-bold">{conflict.field}{conflict.requires_review ? ' — safety-critical' : ''}</span>
                <select className="w-full rounded border bg-white p-2" value={canonicalValues[conflict.field] || ''} onChange={event => setCanonicalValues(values => ({ ...values, [conflict.field]: event.target.value }))}>
                  <option value="">Select canonical value</option>
                  {conflict.values.map(value => <option key={String(value)} value={String(value)}>{String(value)}</option>)}
                </select>
              </label>)}
            </div>}
            {selectedApproval.classification === 'FUNCTIONAL_EQUIVALENT' && (
              <label className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-amber-900">
                <input type="checkbox" className="mt-0.5" checked={functionalEquivalentAcknowledged} onChange={event => setFunctionalEquivalentAcknowledged(event.target.checked)} />
                <span>I approve a substitution recommendation for the documented application. Material identities remain separate.</span>
              </label>
            )}
            {reviewError && <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-rose-700">{reviewError}</div>}
            {selectedApproval.classification === 'FUNCTIONAL_EQUIVALENT' && <label className="block">Application and substitution limitations<textarea className="mt-2 w-full rounded border p-2" value={substitutionConditions} onChange={event => setSubstitutionConditions(event.target.value)} /></label>}
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-[11px] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Approval is recorded with your identity and supporting evidence. Substitution recommendations retain separate material identities.</span>
            </div>
          </div>
        )}
      </Modal>

    </div>
  );
};
