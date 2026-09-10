import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  GitCompare,
  Package,
  Search,
  ShoppingCart,
  Sparkles,
  X,
} from 'lucide-react';
import { materialApi } from '../services/materialApi';
import { matchingApi } from '../services/matchingApi';
import { requestApi } from '../services/requestApi';
import { cpseApi } from '../services/cpseApi';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { Loading } from '../components/common/Loading';
import { getCPSEBadgeColor } from '../utils/formatters';
import { useAuth } from '../hooks/useAuth';
import { hasPermission } from '../utils/permissions';

const scoreColor = (score) => {
  if (score >= 90) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (score >= 70) return 'bg-amber-50 text-amber-700 border-amber-200';
  return 'bg-slate-50 text-slate-700 border-slate-200';
};

export const AIRecommendations = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const canSubmit = hasPermission(user, 'matching.submit');
  const canRequest = hasPermission(user, 'request.create');
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [similarResults, setSimilarResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [matching, setMatching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState('');
  const [submittingId, setSubmittingId] = useState(null);
  const [submittedIds, setSubmittedIds] = useState(new Set());
  const [requestMaterial, setRequestMaterial] = useState(null);
  const [requestingCpse, setRequestingCpse] = useState('');
  const [requestCpses, setRequestCpses] = useState([]);
  const [requestedQuantity, setRequestedQuantity] = useState(1);
  const [requestUom, setRequestUom] = useState('EA');
  const [creatingRequest, setCreatingRequest] = useState(false);

  const handleSearch = async (event) => {
    event.preventDefault();
    const term = query.trim();
    if (!term) return;
    setSearching(true);
    setSearched(true);
    setError('');
    setSelected(null);
    setSimilarResults([]);
    try {
      const response = await materialApi.getMaterials({ search: term });
      setSearchResults((response.data || []).slice(0, 25));
    } catch (err) {
      setSearchResults([]);
      setError(err?.response?.data?.detail || err.message || 'Material search failed.');
    } finally {
      setSearching(false);
    }
  };

  const findSimilar = async (material) => {
    setSelected(material);
    setMatching(true);
    setError('');
    setSimilarResults([]);
    try {
      const response = await matchingApi.findSimilar(material.id, 10);
      setSimilarResults(response.data.items || []);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Unable to find similar materials.');
    } finally {
      setMatching(false);
    }
  };

  const openDirectRequest = async (material) => {
    setError('');
    setRequestMaterial(material);
    setRequestedQuantity(1);
    setRequestUom(material.uom || 'EA');
    try {
      const response = await cpseApi.getAll();
      const cpses = response.data || [];
      setRequestCpses(cpses);
      setRequestingCpse(String(user?.cpse_id || cpses[0]?.id || ''));
    } catch (err) {
      setRequestMaterial(null);
      setError(err?.response?.data?.detail || err.message || 'Unable to load CPSE choices.');
    }
  };

  const createDirectRequest = async (event) => {
    event.preventDefault();
    const quantity = Number(requestedQuantity);
    if (!requestMaterial || !requestingCpse || !Number.isFinite(quantity) || quantity <= 0) {
      setError('Choose a requesting CPSE and enter a quantity greater than zero.');
      return;
    }
    setCreatingRequest(true);
    setError('');
    try {
      const response = await requestApi.createDirectMaterial({
        material_id: requestMaterial.id,
        requesting_cpse_id: Number(requestingCpse),
        requested_quantity: quantity,
        uom: requestUom.trim() || requestMaterial.uom || 'EA',
      });
      setRequestMaterial(null);
      navigate('/requests', { state: { createdRequestId: response.data.request.id } });
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Unable to create the material request.');
    } finally {
      setCreatingRequest(false);
    }
  };

  const compare = (targetCode) => {
    navigate(`/comparison?codeA=${encodeURIComponent(selected.code)}&codeB=${encodeURIComponent(targetCode)}`);
  };

  const submitForApproval = async (result) => {
    setSubmittingId(result.material.id);
    setError('');
    try {
      const response = await matchingApi.submitForApproval(selected.id, result.material.id);
      setSubmittedIds((current) => new Set(current).add(result.material.id));
      if (response.data.status === 'APPROVED') {
        setError('This material pair has already been approved.');
      } else if (response.data.status === 'REJECTED') {
        setError('This material pair was previously rejected.');
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Unable to submit this match for approval.');
    } finally {
      setSubmittingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <Cpu className="h-5 w-5 text-cyan-600" />
          <h2 className="text-xl font-bold tracking-tight text-slate-900">AI Similar Material Search</h2>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Search by material code, product name, description, category, manufacturer, or model, then find the closest compatible products.
        </p>
      </div>

      <form onSubmit={handleSearch} className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
        <label htmlFor="ai-material-search" className="mb-2 block text-xs font-bold text-slate-700">
          Find a product in Material Master
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              id="ai-material-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: COPPER CABLE 4C X 10 SQ MM or NTPC-9380"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button type="submit" icon={Search} loading={searching} disabled={!query.trim()}>
            Search Material
          </Button>
        </div>
      </form>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {searching ? (
        <Loading type="skeleton" rows={4} />
      ) : searched && searchResults.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No Materials Found"
          description="Try a material code or a shorter part of the product description."
        />
      ) : searchResults.length > 0 ? (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Select the source product</h3>
            <span className="text-xs text-slate-500">{searchResults.length} result{searchResults.length === 1 ? '' : 's'}</span>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {searchResults.map((material) => (
              <div
                key={material.id}
                className={`rounded-xl border p-4 text-left transition-all hover:border-blue-300 hover:shadow-sm ${
                  selected?.id === material.id ? 'border-blue-500 bg-blue-50/60 ring-2 ring-blue-100' : 'border-slate-200 bg-white'
                }`}
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${getCPSEBadgeColor(material.cpse)}`}>
                    {material.cpse}
                  </span>
                  <span className="font-mono text-xs font-bold text-blue-700">{material.code}</span>
                </div>
                <p className="text-sm font-bold leading-snug text-slate-900">{material.description}</p>
                <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                  <span>{material.category}</span>
                  <div className="flex items-center gap-2">
                    {canRequest && (
                      <button
                        type="button"
                        onClick={() => openDirectRequest(material)}
                        className="flex items-center gap-1 font-semibold text-emerald-700 hover:text-emerald-900"
                      >
                        <ShoppingCart className="h-3 w-3" /> Request
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => findSimilar(material)}
                      className="flex items-center gap-1 font-semibold text-blue-600 hover:text-blue-800"
                    >
                      Find similar <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {matching ? (
        <Loading type="ai" text={`AI is finding products similar to ${selected?.code || 'the selected material'}...`} />
      ) : selected && similarResults.length === 0 && !error ? (
        <EmptyState
          icon={Sparkles}
          title="No Similar Products Found"
          description="No compatible material in the same product family passed the AI matching threshold."
        />
      ) : similarResults.length > 0 ? (
        <section className="space-y-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Top similar products for {selected.code}</h3>
            <p className="text-xs text-slate-500">Only compatible products that passed AI matching are shown.</p>
          </div>
          <div className="space-y-3">
            {similarResults.map((result, index) => (
              <div key={result.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs">
                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                  <div className="flex min-w-0 gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-50 text-xs font-bold text-cyan-700">
                      {index + 1}
                    </div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className={`rounded border px-2 py-0.5 text-[10px] font-bold ${getCPSEBadgeColor(result.material.cpse_code)}`}>
                          {result.material.cpse_code}
                        </span>
                        <span className="font-mono text-xs font-bold text-blue-700">{result.material.material_code}</span>
                        <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${scoreColor(result.score)}`}>
                          {result.score}% match
                        </span>
                      </div>
                      <p className="mt-2 text-sm font-bold text-slate-900">{result.material.description}</p>
                      <p className="mt-1 text-xs text-slate-500">{result.explanation}</p>
                      <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-500">
                        <span>Category: <strong className="text-slate-700">{result.material.category || '-'}</strong></span>
                        <span>UOM: <strong className="text-slate-700">{result.material.unit || '-'}</strong></span>
                        <span>Classification: <strong className="text-slate-700">{result.classification?.replaceAll('_', ' ') || '-'}</strong></span>
                      </div>
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-wrap gap-2">
                    <Button variant="secondary" size="sm" icon={GitCompare} onClick={() => compare(result.material.material_code)}>
                      Compare
                    </Button>
                    {canSubmit && (
                      <Button
                        variant="success"
                        size="sm"
                        icon={CheckCircle2}
                        loading={submittingId === result.material.id}
                        disabled={submittedIds.has(result.material.id)}
                        onClick={() => submitForApproval(result)}
                      >
                        {submittedIds.has(result.material.id) ? 'Submitted' : 'Submit for Approval'}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {requestMaterial && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4" role="dialog" aria-modal="true" aria-labelledby="direct-request-title">
          <form onSubmit={createDirectRequest} className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 id="direct-request-title" className="text-lg font-bold text-slate-900">Request material</h3>
                <p className="mt-1 text-xs text-slate-500">Create a draft reservation request for the selected mapped material.</p>
              </div>
              <button type="button" onClick={() => setRequestMaterial(null)} className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700" aria-label="Close request form">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="font-mono text-xs font-bold text-blue-700">{requestMaterial.code}</p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{requestMaterial.description}</p>
            </div>
            {error && (
              <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-bold text-slate-700">Requesting CPSE
                <select required value={requestingCpse} onChange={(event) => setRequestingCpse(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal">
                  <option value="">Select CPSE</option>
                  {requestCpses.map((cpse) => <option key={cpse.id} value={cpse.id}>{cpse.code} — {cpse.name}</option>)}
                </select>
              </label>
              <label className="text-xs font-bold text-slate-700">Quantity
                <input required min="0.01" step="any" type="number" value={requestedQuantity} onChange={(event) => setRequestedQuantity(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" />
              </label>
              <label className="text-xs font-bold text-slate-700 sm:col-span-2">Unit of measure
                <input required value={requestUom} onChange={(event) => setRequestUom(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal" />
              </label>
            </div>
            <p className="mt-3 text-[11px] text-slate-500">The request stays in Draft status. You can review and submit it from Material Requests.</p>
            <div className="mt-5 flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={() => setRequestMaterial(null)}>Cancel</Button>
              <Button type="submit" variant="success" icon={ShoppingCart} loading={creatingRequest}>Create draft request</Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
