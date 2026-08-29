import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { GitCompare, ArrowLeft } from 'lucide-react';
import { matchingApi } from '../services/matchingApi';
import { ComparisonPanel } from '../components/matching/ComparisonPanel';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';

export const MaterialComparison = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const codeA = searchParams.get('codeA') || 'MAT-10231';
  const codeB = searchParams.get('codeB') || 'STL-VLV-21';

  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchComparison = async () => {
      setLoading(true);
      try {
        const res = await matchingApi.compareMaterials(codeA, codeB);
        setComparisonData(res.data);
      } catch (err) {
        console.error('Failed to compare materials', err);
      } finally {
        setLoading(false);
      }
    };
    fetchComparison();
  }, [codeA, codeB]);

  const handleCreateMapping = (nationalCode) => {
    navigate(`/approvals?code=${codeA}&nationalCode=${nationalCode}`);
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

      {loading ? (
        <Loading type="ai" text="AI comparing technical specifications & parameters..." />
      ) : (
        <ComparisonPanel
          comparisonData={comparisonData}
          onCreateMapping={handleCreateMapping}
        />
      )}

    </div>
  );
};
