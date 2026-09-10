import { api } from './api';

const text = x => !x ? '' : typeof x === 'string' ? x : Object.entries(x).map(([k, v]) => `${k}: ${v}`).join(', ');

const allNationalMaterials = async () => {
  const rows = [];
  for (let offset = 0; ; offset += 500) {
    const response = await api.get('/api/national-materials', { params: { limit: 500, offset } });
    rows.push(...response.data);
    if (response.data.length < 500) return { data: rows };
  }
};

export const nationalMaterialApi = {
  getNationalMaterials: async (params = {}) => {
    const [r, matRes, cpseRes] = await Promise.all([
      allNationalMaterials(),
      api.get('/api/materials'),
      api.get('/api/cpses')
    ]);
    const mats = matRes.data || [];
    const cpses = cpseRes.data || [];
    const cpseMap = Object.fromEntries(cpses.map(c => [c.id, c]));
    const matMap = Object.fromEntries(mats.map(m => [m.id, m]));

    const list = (r.data || []).map((x) => {
      const mapped = (x.mappings || []).map(mp => {
          const m = matMap[mp.material_id];
          return {
            mappingId: mp.id,
            materialId: mp.material_id,
            cpse: m ? (cpseMap[m.cpse_id]?.code || `CPSE-${m.cpse_id}`) : 'CPSE',
            originalCode: m ? m.material_code : `MAT-${mp.material_id}`,
            description: m ? m.description : '',
            mappedDate: mp.created_at?.split('T')[0] || ''
          };
        });

      return {
        id: x.id,
        nationalCode: x.national_code,
        standardTitle: x.description,
        standardSpecification: text(x.specifications),
        category: x.category || 'General Equipment',
        uom: x.unit || 'EA',
        status: (x.status || 'ACTIVE').toUpperCase(),
        createdDate: x.created_at?.split('T')[0] || '',
        mappedCPSEs: mapped
      };
    });

    let resList = list;
    if (params.search) {
      const q = params.search.toLowerCase();
      resList = resList.filter(x => x.nationalCode?.toLowerCase().includes(q) || x.standardTitle?.toLowerCase().includes(q));
    }
    return { data: resList };
  },

  createNationalMaterial: (d) => api.post('/api/national-materials', {
    description: d.description,
    category: d.category || null,
    unit: d.unit || d.uom || null,
    specifications: d.specifications && typeof d.specifications === 'object' ? d.specifications : (d.specifications ? { text: d.specifications } : {})
  }),

  deleteNationalMaterial: (id) => api.delete(`/api/national-materials/${id}`),
  addMapping: (nationalId, materialId) => api.post(`/api/national-materials/${nationalId}/mappings/${materialId}`),
  removeMapping: (nationalId, materialId) => api.delete(`/api/national-materials/${nationalId}/mappings/${materialId}`),

  getNationalMaterialById: (id) => api.get(`/api/national-materials/${id}`),
  getAvailability: (id) => api.get(`/api/national-materials/${id}/availability`),
  getMaterial360: (id) => api.get(`/api/national-materials/${id}/360`),

  getApprovals: async (status = 'PENDING', page = 1, limit = 25, options = {}) => {
    const params = {
      status,
      page,
      limit,
      sort_by: options.sortBy || 'CONFIDENCE_DESC',
    };
    if (options.classification && options.classification !== 'ALL') {
      params.classification = options.classification;
    }
    const r = await api.get('/api/approvals/paginated', { params });
    const payload = r.data || {};
    return {
      data: (payload.items || []).map(x => {
        const A = x.material_a || {};
        const B = x.material_b || {};
        const p = Number(x.final_score || 0) * (Number(x.final_score || 0) <= 1 ? 100 : 1);
        return {
          id: x.id,
          classification: x.classification,
          materialGroup: A.description || B.description || 'AI Material Match',
          category: A.category || B.category || 'General',
          cpses: [A.cpse_code, B.cpse_code].filter(Boolean),
          originalCodes: [A.material_code, B.material_code].filter(Boolean),
          aiConfidence: Number(p.toFixed(1)),
          recommendation: `${x.classification || 'Unclassified'} — Human review`,
          submittedDate: x.created_at?.replace('T', ' ').slice(0, 16) || '',
          status: x.status,
          evidence: [
            `Semantic similarity ${Number(((x.semantic_score || 0) * 100).toFixed(1))}%`,
            `Attribute similarity ${Number(((x.attribute_score || 0) * 100).toFixed(1))}%`,
            `Fuzzy similarity ${Number(((x.fuzzy_score || 0) * 100).toFixed(1))}%`,
            x.explanation || 'Human validation required'
          ],
          canonicalProposal: x.canonical_proposal || {},
          conflicts: x.canonical_proposal?.conflicts || []
        };
      }),
      pagination: {
        page: payload.page || 1,
        limit: payload.limit || limit,
        total: payload.total || 0,
        pages: payload.pages || 0,
      },
      counts: payload.counts || { PENDING: 0, APPROVED: 0, REJECTED: 0 },
      classificationCounts: payload.classification_counts || { EXACT: 0, NEAR_DUPLICATE: 0, FUNCTIONAL_EQUIVALENT: 0 },
    };
  },

  approveMapping: (id, comment = null, canonicalValues = {}, acknowledgeCriticalConflicts = false, acknowledgeFunctionalEquivalent = false) => api.post(`/api/approvals/${id}/approve`, { comment, canonical_values: canonicalValues, acknowledge_critical_conflicts: acknowledgeCriticalConflicts, acknowledge_functional_equivalent: acknowledgeFunctionalEquivalent }),
  rejectMapping: (id, reason) => api.post(`/api/approvals/${id}/reject`, { comment: reason || null }),

  getAuditTrail: async (filters = {}) => {
    const r = await api.get('/api/audit');
    let l = (r.data || []).map(x => {
      const details = typeof x.details === 'object' && x.details ? x.details : {};
      const msg = details.message || (typeof x.details === 'string' ? x.details : `${x.action} event on ${x.entity_type || 'Entity'} #${x.entity_id ?? ''}`);
      return {
        id: x.id,
        timestamp: x.created_at?.replace('T', ' ').slice(0, 19) || '',
        user: x.user_id ? `User #${x.user_id}` : 'SYSTEM',
        cpse: details.cpse || 'SYSTEM',
        action: x.action,
        materialCode: details.material_code || details.national_code || `${x.entity_type || 'Entity'} #${x.entity_id ?? '-'}`,
        details: msg
      };
    });

    if (filters.cpse && filters.cpse !== 'ALL') {
      l = l.filter(x => x.cpse === filters.cpse);
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      l = l.filter(x => `${x.details} ${x.action} ${x.materialCode} ${x.user}`.toLowerCase().includes(q));
    }
    return { data: l };
  },
  verifyAuditTrail: () => api.get('/api/audit/verify'),
};
