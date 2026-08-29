import { api } from './api';
import { MOCK_MATERIALS } from './materialApi';

export const MOCK_NATIONAL_MATERIALS = [
  {
    id: 'nat-001',
    nationalCode: 'NM-VAL-001',
    standardTitle: 'Industrial Ball Valve SS316 DN50 PN16 Flanged',
    standardSpecification: 'Stainless Steel AISI 316 Body & Trim, Nominal Size DN50 (2 Inch), Pressure Rating PN16 / Class 150, Flanged Ends ANSI B16.5, Fire Tested ISO 10497',
    category: 'Valves & Actuators',
    uom: 'EA',
    status: 'APPROVED',
    aiConfidence: 98.2,
    createdDate: '2026-08-01',
    mappedCPSEs: [
      { cpse: 'ONGC', originalCode: 'MAT-10231', description: 'Industrial Ball Valve SS316 DN50 PN16 Flanged', mappedDate: '2026-08-15' },
      { cpse: 'NTPC', originalCode: 'VLV-77401', description: 'Stainless Steel Ball Valve 50mm Class 150 RF', mappedDate: '2026-08-18' },
      { cpse: 'SAIL', originalCode: 'STL-VLV-21', description: 'Ball Valve SS 316 Class 150 2 Inch Full Port', mappedDate: '2026-08-20' }
    ],
    approvalHistory: [
      { officer: 'Rajesh Kumar (Senior Officer)', action: 'APPROVED', date: '2026-08-20 14:32', comment: 'Specifications and metallurgical grades verified across ONGC, NTPC, and SAIL items.' }
    ]
  },
  {
    id: 'nat-002',
    nationalCode: 'NM-PMP-002',
    standardTitle: 'Centrifugal Heavy Duty Slurry Pump 45kW',
    standardSpecification: 'Flow 120 m3/hr, Total Head 40m, Motor 45kW 415V 50Hz 3-Phase, High Chrome Alloy Casing Hi-Cr28',
    category: 'Pumps & Compressors',
    uom: 'SET',
    status: 'APPROVED',
    aiConfidence: 96.5,
    createdDate: '2026-08-05',
    mappedCPSEs: [
      { cpse: 'ONGC', originalCode: 'MAT-88102', description: 'Centrifugal Slurry Pump 45kW 1450RPM Heavy Duty', mappedDate: '2026-08-10' },
      { cpse: 'CIL', originalCode: 'CIL-PMP-404', description: 'Heavy Duty Submersible Slurry Pump 45kW 50Hz', mappedDate: '2026-08-22' }
    ],
    approvalHistory: [
      { officer: 'Anita Sen (Lead Architect)', action: 'APPROVED', date: '2026-08-23 11:15', comment: 'Harmonized 45kW pump rating and slurry specification across mining and offshore operations.' }
    ]
  },
  {
    id: 'nat-003',
    nationalCode: 'NM-PIP-003',
    standardTitle: 'Carbon Steel Seamless Pipe 6 Inch Sch 40 API 5L Gr B',
    standardSpecification: 'Seamless Carbon Steel, 6" Nominal Bore (150mm), Wall Thickness Schedule 40, Standard API 5L Grade B, Beveled Ends',
    category: 'Pipes & Fittings',
    uom: 'MTR',
    status: 'APPROVED',
    aiConfidence: 99.1,
    createdDate: '2026-08-02',
    mappedCPSEs: [
      { cpse: 'ONGC', originalCode: 'MAT-44102', description: 'Carbon Steel Seamless Pipe 6 Inch Sch 40 API 5L Gr B', mappedDate: '2026-08-05' },
      { cpse: 'SAIL', originalCode: 'STL-PIP-88', description: 'Seamless Steel Line Pipe 150mm Sch 40 Grade B', mappedDate: '2026-08-07' }
    ],
    approvalHistory: [
      { officer: 'Rajesh Kumar (Senior Officer)', action: 'APPROVED', date: '2026-08-07 09:40', comment: 'Exact physical dimensions and API 5L specification match.' }
    ]
  },
  {
    id: 'nat-004',
    nationalCode: 'NM-TRF-004',
    standardTitle: 'Power Transformer 33kV/11kV 5MVA Oil Immersed',
    standardSpecification: 'HV 33kV, LV 11kV, Power Rating 5 MVA, Vector Group Dyn11, Cooling ONAN, CRGO Core Steel, Outdoor Type',
    category: 'Electrical Equipment',
    uom: 'UNIT',
    status: 'APPROVED',
    aiConfidence: 98.4,
    createdDate: '2026-08-12',
    mappedCPSEs: [
      { cpse: 'NTPC', originalCode: 'ELC-33100', description: 'Power Transformer 33kV / 11kV 5MVA Oil Immersed', mappedDate: '2026-08-15' },
      { cpse: 'BHEL', originalCode: 'BHEL-TR-500', description: '33kV / 11kV Step Down Power Transformer 5 MVA ONAN', mappedDate: '2026-08-16' }
    ],
    approvalHistory: [
      { officer: 'V. Raman (Procurement Manager)', action: 'APPROVED', date: '2026-08-16 16:05', comment: 'Verified electrical transformer parameters for NTPC grid integration.' }
    ]
  }
];

export const MOCK_APPROVALS = [
  {
    id: 'app-001',
    materialGroup: 'Industrial SS316 Ball Valve DN50',
    category: 'Valves & Actuators',
    cpses: ['ONGC', 'NTPC', 'SAIL'],
    originalCodes: ['MAT-10231', 'VLV-77401', 'STL-VLV-21'],
    aiConfidence: 97.8,
    recommendation: 'Recommend Merge into National Code NM-VAL-001',
    submittedDate: 'Today, 09:30 AM',
    status: 'PENDING',
    evidence: [
      'Description similarity 98.2%',
      'Specification similarity 96.5%',
      'Category match (Valves & Actuators)',
      'UOM compatibility 100% (EA)'
    ]
  },
  {
    id: 'app-002',
    materialGroup: 'Heavy Duty 45kW Slurry Pump',
    category: 'Pumps & Compressors',
    cpses: ['ONGC', 'CIL'],
    originalCodes: ['MAT-88102', 'CIL-PMP-404'],
    aiConfidence: 88.5,
    recommendation: 'Recommend Merge into National Code NM-PMP-002',
    submittedDate: 'Yesterday, 14:15 PM',
    status: 'PENDING',
    evidence: [
      'Power rating match (45kW 415V 50Hz)',
      'Slurry duty application match',
      'UOM compatibility 100% (SET)',
      'Casing grade evaluation needed'
    ]
  },
  {
    id: 'app-003',
    materialGroup: 'Power Transformer 33kV/11kV 5MVA',
    category: 'Electrical Equipment',
    cpses: ['NTPC', 'BHEL'],
    originalCodes: ['ELC-33100', 'BHEL-TR-500'],
    aiConfidence: 98.4,
    recommendation: 'Recommend Merge into National Code NM-TRF-004',
    submittedDate: '24 Aug 2026',
    status: 'APPROVED',
    evidence: [
      'Voltage ratings match (33kV / 11kV)',
      'MVA capacity match (5 MVA)',
      'Vector group Dyn11 match',
      'ONAN oil cooling match'
    ]
  }
];

export const MOCK_AUDIT_LOGS = [
  { id: 'aud-101', timestamp: '2026-08-27 09:42 AM', user: 'Rajesh Kumar (Senior Officer)', cpse: 'NTPC', action: 'DATA_IMPORT', materialCode: 'materials_ntpc_q3.xlsx', details: 'NTPC imported 4,821 material rows' },
  { id: 'aud-102', timestamp: '2026-08-27 09:44 AM', user: 'SYSTEM (AI Pipeline)', cpse: 'SYSTEM', action: 'VALIDATION', materialCode: 'BATCH-4821', details: 'Validation completed with 4,766 valid records and 55 warnings' },
  { id: 'aud-103', timestamp: '2026-08-27 09:46 AM', user: 'SYSTEM (AI Pipeline)', cpse: 'SYSTEM', action: 'AI_MATCHING', materialCode: 'REC-BATCH-99', details: 'AI generated 283 duplicate candidate recommendation clusters' },
  { id: 'aud-104', timestamp: '2026-08-27 09:50 AM', user: 'Rajesh Kumar (Senior Officer)', cpse: 'ONGC', action: 'OFFICER_REVIEW', materialCode: 'MAT-10231', details: 'Officer reviewed side-by-side comparison with NTPC VLV-77401' },
];

export const nationalMaterialApi = {
  getNationalMaterials: async (params = {}) => {
    try {
      const response = await api.get('/api/national-materials', { params });
      const normalizedData = (response.data || []).map(item => ({
        id: item.id,
        nationalCode: item.nationalCode || item.national_code || 'NM-GEN-001',
        standardTitle: item.standardTitle || item.description || 'Standardized Equipment',
        standardSpecification: item.standardSpecification || item.specifications || 'Standard specifications',
        category: item.category || 'General Equipment',
        uom: item.uom || item.unit || 'EA',
        status: item.status ? item.status.toUpperCase() : 'APPROVED',
        aiConfidence: item.aiConfidence || 98.5,
        createdDate: item.createdDate || (item.created_at ? item.created_at.split('T')[0] : '2026-08-27'),
        mappedCPSEs: item.mappedCPSEs || [],
        approvalHistory: item.approvalHistory || [
          { officer: 'Rajesh Kumar (Senior Officer)', action: 'APPROVED', date: '2026-08-20', comment: 'Harmonized across CPSE material catalog.' }
        ]
      }));
      return { data: normalizedData };
    } catch (err) {
      let list = [...MOCK_NATIONAL_MATERIALS];
      if (params.search) {
        const query = params.search.toLowerCase();
        list = list.filter(m => m.nationalCode.toLowerCase().includes(query) || m.standardTitle.toLowerCase().includes(query));
      }
      return { data: list };
    }
  },

  createNationalMaterial: async (data) => {
    try {
      return await api.post('/api/national-materials', data);
    } catch (err) {
      const newNat = {
        id: `nat-${Date.now()}`,
        nationalCode: `NM-${data.category ? data.category.substring(0, 3).toUpperCase() : 'GEN'}-${Math.floor(100 + Math.random() * 900)}`,
        standardTitle: data.description || 'Standardized Equipment Master',
        standardSpecification: data.specifications || 'Standard specifications',
        category: data.category || 'General Equipment',
        uom: data.unit || 'EA',
        status: 'APPROVED',
        aiConfidence: 99.0,
        createdDate: new Date().toISOString().split('T')[0],
        mappedCPSEs: [],
        approvalHistory: []
      };
      MOCK_NATIONAL_MATERIALS.unshift(newNat);
      return { data: newNat };
    }
  },

  getNationalMaterialById: async (id) => {
    try {
      return await api.get(`/api/national-materials/${id}`);
    } catch (err) {
      const item = MOCK_NATIONAL_MATERIALS.find(m => m.id === id || m.nationalCode === id) || MOCK_NATIONAL_MATERIALS[0];
      return { data: item };
    }
  },

  getApprovals: async () => {
    try {
      return await api.get('/api/approvals');
    } catch (err) {
      return { data: MOCK_APPROVALS };
    }
  },

  approveMapping: async (id) => {
    try {
      return await api.post(`/api/approvals/${id}/approve`);
    } catch (err) {
      const item = MOCK_APPROVALS.find(a => a.id === id);
      if (item) {
        item.status = 'APPROVED';
        if (item.originalCodes) {
          item.originalCodes.forEach(code => {
            const mat = MOCK_MATERIALS.find(m => m.code === code);
            if (mat) mat.matchStatus = 'Matched';
          });
        }
      }
      return { data: { success: true, message: 'Mapping approved and registered to National Material Master.' } };
    }
  },

  rejectMapping: async (id, reason) => {
    try {
      return await api.post(`/api/approvals/${id}/reject`, { reason });
    } catch (err) {
      const item = MOCK_APPROVALS.find(a => a.id === id);
      if (item) item.status = 'REJECTED';
      return { data: { success: true, message: 'Mapping candidate rejected.' } };
    }
  },

  getAuditTrail: async (filters = {}) => {
    try {
      return await api.get('/api/audit-trail', { params: filters });
    } catch (err) {
      let list = [...MOCK_AUDIT_LOGS];
      if (filters.cpse && filters.cpse !== 'ALL') {
        list = list.filter(a => a.cpse === filters.cpse);
      }
      if (filters.search) {
        const q = filters.search.toLowerCase();
        list = list.filter(a => a.details.toLowerCase().includes(q) || a.user.toLowerCase().includes(q) || a.materialCode.toLowerCase().includes(q));
      }
      return { data: list };
    }
  }
};
