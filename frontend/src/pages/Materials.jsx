import { useCallback, useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Plus, Package, Download, AlertCircle } from 'lucide-react';
import { materialApi } from '../services/materialApi';
import { cpseApi } from '../services/cpseApi';
import { MaterialFilters } from '../components/materials/MaterialFilters';
import { MaterialTable } from '../components/materials/MaterialTable';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';
import { useAuth } from '../hooks/useAuth';
import { hasPermission } from '../utils/permissions';

export const Materials = () => {
  const { user } = useAuth();
  const canWrite = hasPermission(user, 'material.write');
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [materials, setMaterials] = useState([]);
  const [cpses, setCpses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [cpse, setCpse] = useState('ALL');
  const [sector, setSector] = useState('ALL');
  const [status, setStatus] = useState('ALL');
  
  // Modals
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // New Material Form
  const [newMaterial, setNewMaterial] = useState({
    code: '',
    description: '',
    cpse: '',
    sector: '',
    category: 'Valves & Actuators',
    specification: '',
    uom: 'EA'
  });

  const loadCpses = useCallback(async () => {
    try {
      const res = await cpseApi.getAll();
      const list = res.data || [];
      setCpses(list);
      if (list.length > 0 && !newMaterial.cpse) {
        const assigned = list.find(item => item.id === user?.cpse_id) || list[0];
        setNewMaterial(prev => ({ ...prev, cpse: assigned.code, sector: assigned.sector }));
      }
    } catch (err) {
      console.error('Failed to load CPSEs', err);
    }
  }, [newMaterial.cpse, user?.cpse_id]);

  const loadMaterials = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await materialApi.getMaterials({ search, cpse, sector, status });
      setMaterials(res.data || []);
    } catch (err) {
      console.error('Failed to load materials', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to load material records from backend.');
    } finally {
      setLoading(false);
    }
  }, [cpse, search, sector, status]);

  useEffect(() => {
    loadCpses();
  }, [loadCpses]);

  useEffect(() => {
    setSearch(searchParams.get('search') || '');
  }, [searchParams]);

  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);

  const handleResetFilters = () => {
    setSearch('');
    setCpse('ALL');
    setSector('ALL');
    setStatus('ALL');
    setSearchParams({});
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    try {
      const matchedCpse = writableCpses.find(c => c.code === newMaterial.cpse);
      if (!matchedCpse) {
        setError('Select a CPSE for the new material.');
        return;
      }
      await materialApi.createMaterial({
        ...newMaterial,
        cpse_id: matchedCpse.id
      });
      setIsAddModalOpen(false);
      setNewMaterial({
        code: '',
        description: '',
        cpse: cpses[0]?.code || '',
        sector: cpses[0]?.sector || '',
        category: 'Valves & Actuators',
        specification: '',
        uom: 'EA'
      });
      loadMaterials();
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create material.');
    }
  };

  const handleCompare = (mat) => {
    navigate(`/comparison?codeA=${mat.code}`);
  };

  const handleMap = (mat) => {
    navigate(`/approvals?code=${mat.code}`);
  };

  const writableCpses = hasPermission(user, '*')
    ? cpses
    : cpses.filter(item => item.id === user?.cpse_id);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Material Master Directory</h2>
          <p className="text-xs text-slate-500 mt-0.5">Central CPSE Inventory records, technical specifications, and AI match status</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" icon={Download} onClick={() => window.print()}>
            Export Master
          </Button>
          {canWrite && (
            <Button variant="primary" size="sm" icon={Plus} onClick={() => setIsAddModalOpen(true)}>
              Add Material
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter Component */}
      <MaterialFilters
        search={search}
        onSearchChange={setSearch}
        cpse={cpse}
        onCpseChange={setCpse}
        sector={sector}
        onSectorChange={setSector}
        status={status}
        onStatusChange={setStatus}
        onReset={handleResetFilters}
        cpses={cpses}
      />

      {/* Material Grid / Table */}
      {loading ? (
        <Loading type="skeleton" rows={6} />
      ) : materials.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No Material Master Records Found"
          description="No materials match your current filter parameters or the repository is empty."
          actionText="Clear Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <MaterialTable
          materials={materials}
          onSelect={setSelectedMaterial}
          onCompare={handleCompare}
          onMap={handleMap}
        />
      )}

      {/* Material Detail Modal */}
      <Modal
        open={!!selectedMaterial}
        onClose={() => setSelectedMaterial(null)}
        title={`Material Master Record: ${selectedMaterial?.code}`}
        subtitle={selectedMaterial?.description}
        maxWidth="max-w-2xl"
        actions={
          <>
            <Button variant="ghost" size="sm" onClick={() => setSelectedMaterial(null)}>Close</Button>
            <Button variant="secondary" size="sm" onClick={() => { setSelectedMaterial(null); handleCompare(selectedMaterial); }}>
              Compare Side-by-Side
            </Button>
          </>
        }
      >
        {selectedMaterial && (
          <div className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-4 bg-slate-50 p-3 rounded-lg border border-slate-100">
              <div>
                <span className="text-slate-400 font-medium block">CPSE Enterprise</span>
                <span className="font-bold text-slate-800">{selectedMaterial.cpse} ({selectedMaterial.sector})</span>
              </div>
              <div>
                <span className="text-slate-400 font-medium block">Category</span>
                <span className="font-bold text-slate-800">{selectedMaterial.category}</span>
              </div>
              <div>
                <span className="text-slate-400 font-medium block">Unit of Measure (UOM)</span>
                <span className="font-bold font-mono text-slate-800">{selectedMaterial.uom}</span>
              </div>
              <div>
                <span className="text-slate-400 font-medium block">Harmonization Status</span>
                <span className="font-bold text-blue-600">{selectedMaterial.matchStatus}</span>
              </div>
            </div>

            <div>
              <span className="text-slate-400 font-medium block mb-1">Technical Specifications & Parameters</span>
              <div className="p-3 bg-slate-900 text-slate-200 rounded-lg font-mono text-xs leading-relaxed">
                {selectedMaterial.specification || 'No extended specifications provided.'}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Add Material Modal */}
      <Modal
        open={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Register New Material Master Record"
        subtitle="Manual entry into CPSE enterprise inventory catalog"
        actions={
          <>
            <Button variant="ghost" size="sm" onClick={() => setIsAddModalOpen(false)}>Cancel</Button>
            <Button variant="primary" size="sm" onClick={handleAddSubmit}>Create Item</Button>
          </>
        }
      >
        <form onSubmit={handleAddSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Material Code</label>
              <input
                type="text"
                required
                placeholder="e.g. MAT-99201"
                value={newMaterial.code}
                onChange={(e) => setNewMaterial({ ...newMaterial, code: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">CPSE Enterprise</label>
              <select
                value={newMaterial.cpse}
                onChange={(e) => {
                  const val = e.target.value;
                  const c = cpses.find(x => x.code === val);
                  setNewMaterial({ ...newMaterial, cpse: val, sector: c?.sector || '' });
                }}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {writableCpses.map((c) => (
                  <option key={c.id} value={c.code}>{c.code} — {c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Material Description</label>
            <input
              type="text"
              required
              placeholder="e.g. Stainless Steel Ball Valve 50mm PN16"
              value={newMaterial.description}
              onChange={(e) => setNewMaterial({ ...newMaterial, description: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Category</label>
              <input
                type="text"
                value={newMaterial.category}
                onChange={(e) => setNewMaterial({ ...newMaterial, category: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">Unit of Measure (UOM)</label>
              <input
                type="text"
                value={newMaterial.uom}
                onChange={(e) => setNewMaterial({ ...newMaterial, uom: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold text-slate-700 mb-1">Technical Specifications</label>
            <textarea
              rows={3}
              placeholder="Detailed parameters, dimensions, pressure ratings, standards..."
              value={newMaterial.specification}
              onChange={(e) => setNewMaterial({ ...newMaterial, specification: e.target.value })}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 font-mono text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};
