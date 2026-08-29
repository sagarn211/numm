import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Cpu, Filter, CheckCircle2, AlertTriangle } from 'lucide-react';
import { matchingApi } from '../services/matchingApi';
import { MatchCard } from '../components/matching/MatchCard';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';

export const AIRecommendations = () => {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL'); // ALL | HIGH | MEDIUM | NEEDS_REVIEW
  const [running, setRunning] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await matchingApi.getRecommendations(filter !== 'ALL' ? { filter } : {});
      setRecommendations(res.data);
    } catch (err) {
      console.error('Failed to load AI recommendations', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  const handleRunMatching = async () => {
    setRunning(true);
    await matchingApi.runMatching();
    await loadData();
    setRunning(false);
  };

  const handleApprove = (id) => {
    setRecommendations(prev => prev.filter(r => r.id !== id));
  };

  const handleReject = (id) => {
    setRecommendations(prev => prev.filter(r => r.id !== id));
  };

  const handleCompare = (codeA, codeB) => {
    navigate(`/comparison?codeA=${codeA}&codeB=${codeB}`);
  };

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Decision Support & Clustering</h2>
          <p className="text-xs text-slate-500 mt-0.5">Automated material master clustering, duplicate identification, and confidence scoring</p>
        </div>
        <Button
          variant="primary"
          size="sm"
          icon={Cpu}
          loading={running}
          onClick={handleRunMatching}
        >
          Run AI Matching Engine
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="bg-white p-2 rounded-xl border border-slate-200/80 shadow-2xs flex items-center gap-2 overflow-x-auto text-xs font-bold">
        <button
          onClick={() => setFilter('ALL')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === 'ALL' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          All Recommendations ({recommendations.length})
        </button>
        <button
          onClick={() => setFilter('HIGH')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
            filter === 'HIGH' ? 'bg-emerald-600 text-white' : 'text-emerald-700 hover:bg-emerald-50'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" /> High Confidence (90%+)
        </button>
        <button
          onClick={() => setFilter('MEDIUM')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
            filter === 'MEDIUM' ? 'bg-amber-600 text-white' : 'text-amber-700 hover:bg-amber-50'
          }`}
        >
          Medium Confidence
        </button>
        <button
          onClick={() => setFilter('NEEDS_REVIEW')}
          className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-1.5 ${
            filter === 'NEEDS_REVIEW' ? 'bg-rose-600 text-white' : 'text-rose-700 hover:bg-rose-50'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" /> Needs Human Review
        </button>
      </div>

      {/* List */}
      {loading ? (
        <Loading type="ai" text="AI Engine clustering material records..." />
      ) : recommendations.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No Candidate Recommendations"
          description="All duplicate candidate clusters in this confidence threshold have been reviewed or resolved."
        />
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <MatchCard
              key={rec.id}
              recommendation={rec}
              onApprove={handleApprove}
              onReject={handleReject}
              onCompare={handleCompare}
            />
          ))}
        </div>
      )}

    </div>
  );
};
