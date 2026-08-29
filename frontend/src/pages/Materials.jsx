import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Plus, Package, Download } from 'lucide-react';
import { materialApi } from '../services/materialApi';
import { MaterialFilters } from '../components/materials/MaterialFilters';
import { MaterialTable } from '../components/materials/MaterialTable';
import { MaterialCard } from '../components/materials/MaterialCard';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import { Loading } from '../components/common/Loading';
import { EmptyState } from '../components/common/EmptyState';

export const Materials = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  
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
    cpse: 'ONGC',
    sector: 'Oil & Gas',
    category: 'Valves & Actuators',
    specification: '',
    uom: 'EA'
  });

  const loadMaterials = async () => {
    setLoading(true);
    try {
      const res = await materialApi.getMaterials({ search, cpse, sector, status });
      setMaterials(res.data);
    } catch (err) {
      console.error('Failed to load materials', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMaterials();
  }, [search, cpse, sector, status]);

  const handleResetFilters = () => {
    setSearch('');
    setCpse('ALL');
    setSector('ALL');
    setStatus('ALL');
    setSearchParams({});
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    await materialApi.createMaterial(newMaterial);
    setIsAddModalOpen(false);
    loadMaterials();
  };

  const handleCompare = (mat) => {
    navigate(`/comparison?codeA=${mat.code}`);
  };

  const handleMap = (mat) => {
    navigate(`/approvals?code=${mat.code}`);
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Material Master Directory</h2>
          <p className="text-xs text-slate-500 mt-0.5">Central CPSE Inventory records, technical specifications, and AI match status</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" icon={Download}>
            Export CSV
          </Button>
          <Button variant="primary" size="sm" icon={Plus} onClick={() => setIsAddModalOpen(true)}>
            Add Material
          </Button>
        </div>
      </div>

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
      />

      {/* Table or Loading */}
      {loading ? (
        <Loading type="skeleton" rows={6} />
      ) : materials.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No Material Items Found"
          description="No materials match your specified CPSE or category filters. Try clearing your search parameters."
          actionLabel="Reset Search Filters"
          onAction={handleResetFilters}
        />
      ) : (
        <MaterialTable
          materials={materials}
          onSelectMaterial={setSelectedMaterial}
          onCompareMaterial={handleCompare}
          onMapMaterial={handleMap}
        />
      )}

      {/* Detail Modal Drawer */}
      <MaterialCard
        material={selectedMaterial}
        open={!!selectedMaterial}
        onClose={() => setSelectedMaterial(null)}
        onCompare={handleCompare}
        onMap={handleMap}
      />

      {/* Add Material Modal */}
      <Modal
        open={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Register New Material Record"
        subtitle="Manual entry for CPSE material master item"
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
                onChange={(e) => setNewMaterial({ ...newMaterial, cpse: e.target.value })}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-slate-900 font-bold focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ONGC">ONGC</option>
                <option value="NTPC">NTPC</option>
                <option value="SAIL">SAIL</option>
                <option value="CIL">CIL</option>
                <option value="BHEL">BHEL</option>
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
