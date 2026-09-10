import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { GitCompare, ArrowLeft, AlertCircle } from 'lucide-react';
import { matchingApi } from '../services/matchingApi';
import { materialApi } from '../services/materialApi';
import { ComparisonPanel } from '../components/matching/ComparisonPanel';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';

export const MaterialComparison = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [materials, setMaterials] = useState([]);
  const [codeA, setCodeA] = useState(searchParams.get('codeA') || '');
  const [codeB, setCodeB] = useState(searchParams.get('codeB') || '');
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const comparisonRequestId = useRef(0);
  const queryCodeA = searchParams.get('codeA');
  const queryCodeB = searchParams.get('codeB');

  useEffect(() => {
    materialApi.getMaterials()
      .then(res => setMaterials(res.data || []))
      .catch(err => console.error('Failed to load materials for comparison', err));
  }, []);

  const runComparison = useCallback(async (a, b) => {
    const requestId = ++comparisonRequestId.current;
    if (!a || !b) {
      setComparisonData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await matchingApi.compareMaterials(a, b);
      if (requestId === comparisonRequestId.current) {
        setComparisonData(res.data);
      }
    } catch (err) {
      if (requestId !== comparisonRequestId.current) return;
      console.error('Failed to compare materials', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to compare selected materials.');
      setComparisonData(null);
    } finally {
      if (requestId === comparisonRequestId.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (!queryCodeA || !queryCodeB) return;
    setCodeA(queryCodeA);
    setCodeB(queryCodeB);
    runComparison(queryCodeA, queryCodeB);
  }, [queryCodeA, queryCodeB, runComparison]);

  useEffect(() => {
    if (queryCodeA || queryCodeB) return;
    if (materials.length >= 2 && !codeA && !codeB) {
      setCodeA(materials[0].code);
      setCodeB(materials[1].code);
      runComparison(materials[0].code, materials[1].code);
    }
  }, [materials, queryCodeA, queryCodeB, codeA, codeB, runComparison]);

  const handleCompareSubmit = (e) => {
    e.preventDefault();
    if (codeA && codeB) {
      setSearchParams({ codeA, codeB });
    }
  };

  const handleCreateMapping = (nationalCode) => {
    navigate(`/approvals?code=${codeA}&nationalCode=${nationalCode || ''}`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <button
              onClick={() => navigate(-1)}
              className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back
            </button>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Material Parameter Comparison Workspace</h2>
          <p className="text-xs text-slate-500">Side-by-side technical evaluation for cross-CPSE material harmonization</p>
        </div>
      </div>

      {/* Select Materials Bar */}
      <form onSubmit={handleCompareSubmit} className="bg-white border rounded-xl p-4 grid md:grid-cols-5 gap-3 items-end shadow-2xs">
        <div className="md:col-span-2">
          <label className="block text-xs font-bold text-slate-700 mb-1">Source Material A</label>
          <select
            value={codeA}
            onChange={(e) => setCodeA(e.target.value)}
            className="w-full bg-slate-50 border rounded-lg px-3 py-2 text-xs font-semibold text-slate-900"
          >
            <option value="">Select Material A</option>
            {materials.map((m) => (
              <option key={m.id} value={m.code}>
                [{m.cpse}] {m.code} — {m.description}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="block text-xs font-bold text-slate-700 mb-1">Source Material B</label>
          <select
            value={codeB}
            onChange={(e) => setCodeB(e.target.value)}
            className="w-full bg-slate-50 border rounded-lg px-3 py-2 text-xs font-semibold text-slate-900"
          >
            <option value="">Select Material B</option>
            {materials.map((m) => (
              <option key={m.id} value={m.code}>
                [{m.cpse}] {m.code} — {m.description}
              </option>
            ))}
          </select>
        </div>

        <div>
          <Button variant="primary" icon={GitCompare} type="submit" loading={loading} className="w-full">
            Compare
          </Button>
        </div>
      </form>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <Loading type="ai" text="AI comparing technical specifications & parameters..." />
      ) : comparisonData ? (
        <ComparisonPanel
          comparisonData={comparisonData}
          onCreateMapping={handleCreateMapping}
        />
      ) : (
        <div className="bg-white border rounded-xl p-12 text-center text-slate-400">
          <GitCompare className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm font-bold text-slate-600">Select two materials to compare</p>
          <p className="text-xs text-slate-400 mt-1">Side-by-side technical parameter audit and AI harmonization verdict will be displayed.</p>
        </div>
      )}
    </div>
  );
};
