import { api } from './api';
const specsText = (x) => !x ? '' : typeof x === 'string' ? x : Object.entries(x).map(([k,v]) => `${k}: ${v}`).join(', ');
const cpseMap = async () => { try { const r=await api.get('/api/cpses'); return Object.fromEntries((r.data||[]).map(c=>[c.id,c])); } catch (error) { console.error('Failed to load CPSE metadata', error); throw error; } };
export const normalizeMaterial = (m,c={}) => ({
  id:m.id, code:m.material_code, material_code:m.material_code, description:m.description,
  cpse:c[m.cpse_id]?.code || `CPSE-${m.cpse_id}`, cpseId:m.cpse_id, sector:c[m.cpse_id]?.sector || '',
  category:m.category || 'General', subcategory:m.subcategory || 'Unspecified', classificationSource:m.classification_source || null, specification:specsText(m.specifications), specifications:m.specifications || {},
  uom:m.unit || 'EA', matchStatus:m.matching_status || 'NOT_PROCESSED', nationalCode:m.national_code || null,
  confidence:m.classification_confidence == null ? null : Number(m.classification_confidence) * 100, createdDate:m.created_at?.split('T')[0] || '', lastUpdated:m.updated_at?.split('T')[0] || '',
  grade:m.specifications?.grade || m.specifications?.material_grade || '-', size:m.specifications?.size || m.specifications?.dimensions || '-',
  manufacturer:m.manufacturer || '-', model:m.model || null, source:m.source, status:m.status,
});

const firstDefined = (...values) => values.find((value) => value !== undefined);
const toBackendMaterial = (data, { create = false } = {}) => {
  const cpseId = firstDefined(data.cpse_id, data.cpseId);
  const specification = firstDefined(
    data.specifications,
    data.specification !== undefined ? { text: data.specification } : undefined,
  );
  const payload = {
    cpse_id: cpseId === undefined ? undefined : Number(cpseId),
    material_code: firstDefined(data.material_code, data.code),
    description: data.description,
    category: data.category,
    unit: firstDefined(data.unit, data.uom),
    manufacturer: data.manufacturer,
    model: data.model,
    specifications: specification,
    source: firstDefined(data.source, create ? 'MANUAL' : undefined),
  };
  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== undefined),
  );
};

export const materialApi = {
  getMaterials: async (params={}) => {
    const [r,c] = await Promise.all([api.get('/api/materials',{params:{search:params.search||undefined,cpse_id:params.cpse_id||undefined,category:params.category||undefined}}), cpseMap()]);
    let list=(r.data||[]).map(m=>normalizeMaterial(m,c));
    if(params.cpse && params.cpse!=='ALL') list=list.filter(m=>m.cpse===params.cpse);
    if(params.sector && params.sector!=='ALL') list=list.filter(m=>m.sector===params.sector);
    if(params.status && params.status!=='ALL') {
      const statuses = {
        Matched: ['PROCESSED'],
        'Pending Review': ['PROCESSING'],
        Unmatched: ['NOT_PROCESSED', 'FAILED'],
      }[params.status] || [];
      list=list.filter(m=>statuses.includes(m.matchStatus));
    }
    return {data:list};
  },
  getMaterialById: async (id) => { const [r,c]=await Promise.all([api.get(`/api/materials/${id}`),cpseMap()]); return {data:normalizeMaterial(r.data,c)}; },
  createMaterial: (data) => api.post('/api/materials', toBackendMaterial(data, { create: true })),
  updateMaterial: (id, data) => api.put(`/api/materials/${id}`, toBackendMaterial(data)),
  deleteMaterial:(id)=>api.delete(`/api/materials/${id}`),
};
