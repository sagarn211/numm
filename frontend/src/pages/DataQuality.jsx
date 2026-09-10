import { useEffect, useState } from 'react';
import { ShieldCheck } from 'lucide-react';
import { dataQualityApi } from '../services/dataQualityApi';

export const DataQuality = () => {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    dataQualityApi.getMetrics()
      .then(response => setMetrics(response.data))
      .catch(requestError => setError(requestError?.response?.data?.detail || requestError.message));
  }, []);

  const metricRows = metrics ? [
    ['Description', metrics.description_completeness],
    ['Category', metrics.category_completeness],
    ['Automatic classification', metrics.automatic_classification_coverage],
    ['UOM', metrics.uom_completeness],
    ['Manufacturer', metrics.manufacturer_completeness],
    ['Mapping coverage', metrics.mapping_coverage],
    ['Required technical attributes', metrics.technical_readiness_percent],
  ] : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Data Quality</h2>
        <p className="text-xs text-slate-500">Live completeness, classification and harmonization metrics</p>
      </div>
      {error && <div className="p-3 bg-rose-50 text-rose-700 rounded-lg text-xs">{error}</div>}
      {!metrics && !error && <div className="p-8 text-center text-slate-500">Loading data-quality metrics…</div>}
      {metrics && (
        <>
          <div className="bg-slate-900 text-white rounded-2xl p-6 flex justify-between">
            <div>
              <div className="text-xs text-cyan-300 uppercase font-bold">Overall score</div>
              <div className="text-5xl font-black mt-2">{Number(metrics.data_quality_score || 0)}%</div>
              <div className="text-xs text-slate-400">{Number(metrics.total_materials || 0)} materials</div>
            </div>
            <ShieldCheck className="w-16 h-16 text-cyan-400" />
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {metricRows.map(([name, rawValue]) => {
              const value = Number(rawValue || 0);
              return (
                <div key={name} className="bg-white border rounded-xl p-5">
                  <div className="flex justify-between text-xs font-bold">
                    <span>{name}</span><span>{value}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded mt-3">
                    <div className="h-2 bg-blue-600 rounded" style={{ width: `${Math.min(value, 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <section className="rounded border bg-white p-4"><h3 className="font-bold">Technical evidence to complete</h3><p className="text-xs">First 100 records requiring attributes or a category schema.</p>{(metrics.technical_issues || []).map(row => <div key={row.material_id} className="border-t py-2 text-xs"><strong>{row.material_code}</strong>: {row.schema_supported ? row.missing_attributes.join(', ') : 'Category schema requires engineering definition'}</div>)}</section>
        </>
      )}
    </div>
  );
};
