import React, { useEffect, useState } from 'react';
import { Globe2, Search, CheckCircle2, Network, ShieldCheck, FileText, ExternalLink, Plus } from 'lucide-react';
import { nationalMaterialApi } from '../services/nationalMaterialApi';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { getCPSEBadgeColor, formatConfidence } from '../utils/formatters';

export const NationalMaterials = () => {
  const [materials, setMaterials] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedNational, setSelectedNational] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  const [newCode, setNewCode] = useState({
    description: '',
    category: 'Valves & Actuators',
    unit: 'NOS',
    specifications: ''
  });

  const loadNationalData = async () => {
    setLoading(true);
    try {
      const res = await nationalMaterialApi.getNationalMaterials({ search });
      setMaterials(res.data);
    } catch (err) {
      console.error('Failed to load National materials', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNationalData();
  }, [search]);

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    await nationalMaterialApi.createNationalMaterial(newCode);
    setIsAddModalOpen(false);
    setNewCode({ description: '', category: 'Valves & Actuators', unit: 'NOS', specifications: '' });
    loadNationalData();
  };

  return (
    <div className="space-y-6">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">National Material Master Registry</h2>
          <p className="text-xs text-slate-500 mt-0.5">Official unified material codes mapped across Indian CPSE enterprises</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-full md:w-64">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search national code or description..."
                className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <Button variant="primary" size="sm" icon={Plus} onClick={() => setIsAddModalOpen(true)}>
            Create National Code
          </Button>
        </div>
      </div>

      {/* Grid of Large National Material Cards */}
      {loading ? (
        <Loading type="skeleton" rows={4} />
      ) : materials.length === 0 ? (
        <EmptyState
          icon={Globe2}
          title="No National Material Codes Found"
          description="Try modifying your search term."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {materials.map((nat) => (
            <div
              key={nat.id}
              className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Code & Badge Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono font-black text-cyan-800 bg-cyan-50 border border-cyan-200 px-3 py-1 rounded-lg">
                      {nat.nationalCode}
                    </span>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> {nat.status}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-slate-500">
                    AI Confidence: <strong className="text-emerald-600">{formatConfidence(nat.aiConfidence)}</strong>
                  </span>
                </div>

                <h3 className="text-base font-bold text-slate-900">{nat.standardTitle}</h3>
                <p className="text-xs text-slate-500 mt-1">Category: {nat.category} • UOM: {nat.uom}</p>

                {/* Specification Teaser */}
                <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-100 font-mono text-[11px] text-slate-700 line-clamp-2">
                  {nat.standardSpecification}
                </div>

                {/* Mapped CPSE Tags */}
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <div className="text-[10px] font-bold text-slate-400 uppercase mb-2">Mapped CPSE Original Codes</div>
                  <div className="flex flex-wrap gap-2">
                    {(nat.mappedCPSEs || []).map((m, idx) => {
                      const badgeClass = getCPSEBadgeColor(m.cpse);
                      return (
                        <div key={idx} className="flex items-center gap-1.5 bg-slate-50 border border-slate-200/80 px-2.5 py-1 rounded-lg text-xs font-mono">
                          <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${badgeClass}`}>
                            {m.cpse}
                          </span>
                          <span className="font-bold text-slate-800">{m.originalCode}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Bottom Action Trigger */}
              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-400">Created: {nat.createdDate}</span>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={Network}
                  onClick={() => setSelectedNational(nat)}
                >
                  View Mapping Network →
                </Button>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Detail Modal for National Material Network */}
      <Modal
        open={!!selectedNational}
        onClose={() => setSelectedNational(null)}
        title={`National Material Registry: ${selectedNational?.nationalCode}`}
        subtitle={selectedNational?.standardTitle}
        maxWidth="max-w-3xl"
        actions={
          <Button variant="primary" size="sm" onClick={() => setSelectedNational(null)}>
            Close Registry Record
          </Button>
        }
      >
        {selectedNational && (
          <div className="space-y-5 text-xs">
            {/* Master Spec */}
            <div className="p-4 rounded-xl bg-slate-900 text-slate-200 border border-slate-800">
              <div className="text-[10px] font-bold text-cyan-400 uppercase font-mono mb-1">Standardized National Specification</div>
              <p className="font-mono text-xs leading-relaxed">{selectedNational.standardSpecification}</p>
            </div>

            {/* Mapped CPSE List */}
            <div>
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                Harmonized CPSE Material Mappings ({(selectedNational.mappedCPSEs || []).length} Participating CPSEs)
              </h4>
              <div className="space-y-2">
                {(selectedNational.mappedCPSEs || []).map((m, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getCPSEBadgeColor(m.cpse)}`}>
                        {m.cpse}
                      </span>
                      <div>
                        <div className="font-mono font-bold text-blue-600">{m.originalCode}</div>
                        <div className="text-slate-600 text-[11px]">{m.description}</div>
                      </div>
                    </div>
                    <span className="text-[10px] text-slate-400 font-mono">Mapped: {m.mappedDate}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Governance History */}
            <div>
              <h4 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] mb-2">
                Approval & Audit Governance Log
              </h4>
              <div className="space-y-1.5">
                {selectedNational.approvalHistory?.map((h, idx) => (
                  <div key={idx} className="p-2.5 bg-emerald-50/60 border border-emerald-200 rounded-lg text-emerald-900 font-medium">
                    <div className="flex items-center justify-between font-bold text-[11px]">
                      <span>{h.officer}</span>
                      <span className="font-mono">{h.date}</span>
                    </div>
                    <p className="text-[11px] text-emerald-800 mt-1">{h.comment}</p>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </Modal>

      {/* Create National Code Modal */}
      <Modal
        open={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Generate New National Material Master Code"
        subtitle="Standardized master entry for National Material Registry"
        actions={
          <>
            <Button variant="ghost" size="sm" onClick={() => setIsAddModalOpen(false)}>Cancel</Button>
            <Button variant="primary" size="sm" onClick={handleCreateSubmit}>Generate National Code</Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-bold text-slate-700 mb-1">Standard Material Description</label>
            <input
              type="text"
              required
              placeholder="e.g. Centrifugal Heavy Duty Slurry Pump 45kW 1450RPM"
              value={newCode.description}
              onChange={(e) => setNewCode({ ...newCode, description: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Category</label>
              <select
                value={newCode.category}
                onChange={(e) => setNewCode({ ...newCode, category: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Valves & Actuators">Valves & Actuators</option>
                <option value="Pumps & Compressors">Pumps & Compressors</option>
                <option value="Pipes & Fittings">Pipes & Fittings</option>
                <option value="Electrical Equipment">Electrical Equipment</option>
                <option value="Bearings & Power Transmission">Bearings & Power Transmission</option>
              </select>
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">Standard UOM</label>
              <input
                type="text"
                value={newCode.unit}
                onChange={(e) => setNewCode({ ...newCode, unit: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Standard National Specifications</label>
            <textarea
              rows={3}
              placeholder="Harmonized technical specifications across participating CPSEs..."
              value={newCode.specifications}
              onChange={(e) => setNewCode({ ...newCode, specifications: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </form>
      </Modal>

    </div>
  );
};
