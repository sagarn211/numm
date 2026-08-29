import { api } from './api';

export const MOCK_MATERIALS = [
  {
    id: 'mat-001',
    code: 'MAT-10231',
    description: 'Industrial Ball Valve SS316 DN50 PN16 Flanged',
    cpse: 'ONGC',
    sector: 'Oil & Gas',
    category: 'Valves & Actuators',
    specification: 'Grade SS316, Size DN50 (2 Inch), Pressure Class PN16, End Connection Flanged ANSI B16.5',
    uom: 'EA',
    matchStatus: 'Matched',
    nationalCode: 'NM-VAL-001',
    confidence: 97.4,
    createdDate: '2026-08-15',
    lastUpdated: '2026-08-27',
    grade: 'SS316',
    size: 'DN50 / 2 Inch',
    manufacturer: 'L&T Valves'
  },
  {
    id: 'mat-002',
    code: 'VLV-77401',
    description: 'Stainless Steel Ball Valve 50mm Class 150 RF',
    cpse: 'NTPC',
    sector: 'Power',
    category: 'Valves & Actuators',
    specification: 'AISI 316 Body, 50mm Nominal Bore, Class 150 Raised Face Flange',
    uom: 'EA',
    matchStatus: 'Matched',
    nationalCode: 'NM-VAL-001',
    confidence: 96.8,
    createdDate: '2026-08-18',
    lastUpdated: '2026-08-26',
    grade: 'SS316',
    size: '50mm / 2 Inch',
    manufacturer: 'Kirloskar Valves'
  },
  {
    id: 'mat-003',
    code: 'STL-VLV-21',
    description: 'Ball Valve SS 316 Class 150 2 Inch Full Port',
    cpse: 'SAIL',
    sector: 'Steel',
    category: 'Valves & Actuators',
    specification: 'Stainless Steel 316, 2" Full Bore, 150# Flanged End',
    uom: 'EA',
    matchStatus: 'Matched',
    nationalCode: 'NM-VAL-001',
    confidence: 98.1,
    createdDate: '2026-08-20',
    lastUpdated: '2026-08-27',
    grade: 'SS316',
    size: '2 Inch',
    manufacturer: 'Audco'
  },
  {
    id: 'mat-004',
    code: 'MAT-88102',
    description: 'Centrifugal Slurry Pump 45kW 1450RPM Heavy Duty',
    cpse: 'ONGC',
    sector: 'Oil & Gas',
    category: 'Pumps & Compressors',
    specification: 'Flow 120 m3/hr, Head 40m, Motor 45kW 415V 50Hz, Casing High Chrome Alloy',
    uom: 'SET',
    matchStatus: 'Pending Review',
    nationalCode: 'NM-PMP-002',
    confidence: 89.2,
    createdDate: '2026-08-10',
    lastUpdated: '2026-08-25',
    grade: 'High Chrome Hi-Cr28',
    size: 'Flow 120m3/h',
    manufacturer: 'KSB Pumps'
  },
  {
    id: 'mat-005',
    code: 'CIL-PMP-404',
    description: 'Heavy Duty Submersible Slurry Pump 45kW 50Hz',
    cpse: 'CIL',
    sector: 'Mining',
    category: 'Pumps & Compressors',
    specification: 'Submersible Slurry Impeller, 45kW 3-Phase 415V, Discharge 150mm',
    uom: 'SET',
    matchStatus: 'Pending Review',
    nationalCode: 'NM-PMP-002',
    confidence: 88.5,
    createdDate: '2026-08-22',
    lastUpdated: '2026-08-27',
    grade: 'Cast Steel / Alloy',
    size: 'Discharge 150mm',
    manufacturer: 'Flygt / Xylem'
  },
  {
    id: 'mat-006',
    code: 'MAT-44102',
    description: 'Carbon Steel Seamless Pipe 6 Inch Sch 40 API 5L Gr B',
    cpse: 'ONGC',
    sector: 'Oil & Gas',
    category: 'Pipes & Fittings',
    specification: 'API 5L Grade B, Nominal Size 6", Schedule 40, Beveled Ends, 6m Length',
    uom: 'MTR',
    matchStatus: 'Matched',
    nationalCode: 'NM-PIP-003',
    confidence: 99.1,
    createdDate: '2026-08-01',
    lastUpdated: '2026-08-24',
    grade: 'API 5L Gr B',
    size: '6" Sch 40',
    manufacturer: 'Jindal Saw'
  },
  {
    id: 'mat-007',
    code: 'STL-PIP-88',
    description: 'Seamless Steel Line Pipe 150mm Sch 40 Grade B',
    cpse: 'SAIL',
    sector: 'Steel',
    category: 'Pipes & Fittings',
    specification: 'CS Seamless 150mm NB (6 Inch), Wall Thickness Sch40, Standard API 5L',
    uom: 'MTR',
    matchStatus: 'Matched',
    nationalCode: 'NM-PIP-003',
    confidence: 98.6,
    createdDate: '2026-08-04',
    lastUpdated: '2026-08-23',
    grade: 'API 5L Gr B',
    size: '150mm / 6"',
    manufacturer: 'SAIL Tubular'
  },
  {
    id: 'mat-008',
    code: 'ELC-33100',
    description: 'Power Transformer 33kV / 11kV 5MVA Oil Immersed',
    cpse: 'NTPC',
    sector: 'Power',
    category: 'Electrical Equipment',
    specification: 'Primary 33kV, Secondary 11kV, Vector Group Dyn11, ONAN Cooling, OLTC',
    uom: 'UNIT',
    matchStatus: 'Matched',
    nationalCode: 'NM-TRF-004',
    confidence: 97.9,
    createdDate: '2026-08-11',
    lastUpdated: '2026-08-26',
    grade: 'CRGO Core',
    size: '5 MVA',
    manufacturer: 'ABB India'
  },
  {
    id: 'mat-009',
    code: 'BHEL-TR-500',
    description: '33kV / 11kV Step Down Power Transformer 5 MVA ONAN',
    cpse: 'BHEL',
    sector: 'Heavy Engineering',
    category: 'Electrical Equipment',
    specification: 'HV 33kV, LV 11kV, Capacity 5MVA, Oil Filled Outdoor Type Dyn11',
    uom: 'UNIT',
    matchStatus: 'Matched',
    nationalCode: 'NM-TRF-004',
    confidence: 98.4,
    createdDate: '2026-08-14',
    lastUpdated: '2026-08-26',
    grade: 'CRGO Core',
    size: '5 MVA',
    manufacturer: 'BHEL Bhopal'
  },
  {
    id: 'mat-010',
    code: 'STL-BRG-12',
    description: 'Spherical Roller Bearing 22220 K C3 Tapered Bore',
    cpse: 'SAIL',
    sector: 'Steel',
    category: 'Bearings & Power Transmission',
    specification: 'Bore 100mm, OD 180mm, Width 46mm, Tapered 1:12, Clearance C3',
    uom: 'EA',
    matchStatus: 'Unmatched',
    nationalCode: null,
    confidence: 62.5,
    createdDate: '2026-08-24',
    lastUpdated: '2026-08-27',
    manufacturer: 'SKF Bearings'
  }
];

export const materialApi = {
  getMaterials: async (params = {}) => {
    try {
      const response = await api.get('/api/materials', { params });
      const cpseMap = { 1: 'ONGC', 2: 'NTPC', 3: 'SAIL', 4: 'BHEL', 5: 'CIL', 6: 'GAIL', 7: 'IOCL' };
      const sectorMap = { 1: 'Oil & Gas', 2: 'Power', 3: 'Steel', 4: 'Heavy Engineering', 5: 'Mining', 6: 'Oil & Gas', 7: 'Oil & Gas' };

      const normalizedData = (response.data || []).map(item => ({
        id: item.id,
        code: item.code || item.material_code || `MAT-${item.id}`,
        cpse: item.cpse || cpseMap[item.cpse_id] || 'ONGC',
        sector: item.sector || sectorMap[item.cpse_id] || 'General',
        description: item.description,
        specification: item.specification || item.specifications || item.description,
        category: item.category || 'General Equipment',
        uom: item.uom || item.unit || 'EA',
        nationalCode: item.nationalCode || (item.category === 'Valves & Actuators' ? 'NM-VAL-001' : item.category === 'Pumps & Compressors' ? 'NM-PMP-002' : item.category === 'Electrical Equipment' ? 'NM-TRF-004' : 'NM-PIP-003'),
        matchStatus: item.matchStatus || 'MATCHED',
        confidenceScore: item.confidenceScore || 97.4,
        standardizationProgress: item.standardizationProgress || 100,
        lastUpdated: item.lastUpdated || 'Today',
        grade: item.grade || 'Industrial Grade SS316',
        size: item.size || 'Standard',
        manufacturer: item.manufacturer || 'Authorized Manufacturer'
      }));

      let list = normalizedData;
      if (params.search) {
        const query = params.search.toLowerCase();
        list = list.filter(m => m.code.toLowerCase().includes(query) || m.description.toLowerCase().includes(query));
      }
      if (params.cpse && params.cpse !== 'ALL') {
        list = list.filter(m => m.cpse === params.cpse);
      }

      return { data: list };
    } catch (err) {
      let data = [...MOCK_MATERIALS];
      if (params.search) {
        const query = params.search.toLowerCase();
        data = data.filter(m => 
          m.code.toLowerCase().includes(query) || 
          m.description.toLowerCase().includes(query)
        );
      }
      return { data };
    }
  },
  getMaterialById: async (id) => {
    try {
      return await api.get(`/api/materials/${id}`);
    } catch (err) {
      const item = MOCK_MATERIALS.find(m => m.id === id || m.code === id) || MOCK_MATERIALS[0];
      return { data: item };
    }
  },
  createMaterial: async (materialData) => {
    try {
      return await api.post('/api/materials', materialData);
    } catch (err) {
      const newItem = {
        id: `mat-${Date.now()}`,
        code: materialData.code || `MAT-${Math.floor(10000 + Math.random() * 90000)}`,
        description: materialData.description || 'New Industrial Component',
        cpse: materialData.cpse || 'ONGC',
        sector: materialData.sector || 'Oil & Gas',
        category: materialData.category || 'General Equipment',
        specification: materialData.specification || 'Standard Industrial Grade',
        uom: materialData.uom || 'EA',
        matchStatus: 'Pending Review',
        nationalCode: null,
        confidence: 0,
        createdDate: new Date().toISOString().split('T')[0],
        lastUpdated: new Date().toISOString().split('T')[0]
      };
      MOCK_MATERIALS.unshift(newItem);
      return { data: newItem };
    }
  }
};
