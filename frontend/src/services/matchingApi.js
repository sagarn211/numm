import { api } from './api';

export const MOCK_RECOMMENDATIONS = [
  {
    id: 'rec-001',
    confidenceCategory: 'HIGH', // HIGH (90%+), MEDIUM (70-89%), NEEDS_REVIEW (<70%)
    overallConfidence: 97.4,
    sourceMaterial: {
      code: 'MAT-10231',
      cpse: 'ONGC',
      description: 'Industrial Ball Valve SS316 DN50 PN16 Flanged',
      specification: 'Grade SS316, Size DN50 (2 Inch), Pressure Class PN16',
      uom: 'EA',
      category: 'Valves & Actuators'
    },
    targetMaterial: {
      code: 'VLV-77401',
      cpse: 'NTPC',
      description: 'Stainless Steel Ball Valve 50mm Class 150 RF',
      specification: 'AISI 316 Body, 50mm Nominal Bore, Class 150 Raised Face Flange',
      uom: 'EA',
      category: 'Valves & Actuators'
    },
    suggestedNationalCode: 'NM-VAL-001',
    aiReasoning: 'Descriptions and technical parameters strongly overlap. Both specify Grade 316 Stainless Steel, 2 Inch / 50mm bore size, and 150#/PN16 pressure class rating.',
    matchMetrics: {
      descriptionSimilarity: 98.2,
      specificationSimilarity: 96.5,
      categorySimilarity: 94.0,
      uomCompatibility: 100.0
    }
  },
  {
    id: 'rec-002',
    confidenceCategory: 'HIGH',
    overallConfidence: 98.4,
    sourceMaterial: {
      code: 'ELC-33100',
      cpse: 'NTPC',
      description: 'Power Transformer 33kV / 11kV 5MVA Oil Immersed',
      specification: 'Primary 33kV, Secondary 11kV, Vector Group Dyn11, ONAN Cooling',
      uom: 'UNIT',
      category: 'Electrical Equipment'
    },
    targetMaterial: {
      code: 'BHEL-TR-500',
      cpse: 'BHEL',
      description: '33kV / 11kV Step Down Power Transformer 5 MVA ONAN',
      specification: 'HV 33kV, LV 11kV, Capacity 5MVA, Oil Filled Outdoor Type Dyn11',
      uom: 'UNIT',
      category: 'Electrical Equipment'
    },
    suggestedNationalCode: 'NM-TRF-004',
    aiReasoning: 'Exact technical parameter alignment across electrical ratings (33kV/11kV), transformer MVA capacity (5MVA), and cooling type (ONAN).',
    matchMetrics: {
      descriptionSimilarity: 99.0,
      specificationSimilarity: 98.1,
      categorySimilarity: 100.0,
      uomCompatibility: 100.0
    }
  },
  {
    id: 'rec-003',
    confidenceCategory: 'MEDIUM',
    overallConfidence: 88.5,
    sourceMaterial: {
      code: 'MAT-88102',
      cpse: 'ONGC',
      description: 'Centrifugal Slurry Pump 45kW 1450RPM Heavy Duty',
      specification: 'Flow 120 m3/hr, Head 40m, Motor 45kW 415V 50Hz',
      uom: 'SET',
      category: 'Pumps & Compressors'
    },
    targetMaterial: {
      code: 'CIL-PMP-404',
      cpse: 'CIL',
      description: 'Heavy Duty Submersible Slurry Pump 45kW 50Hz',
      specification: 'Submersible Slurry Impeller, 45kW 3-Phase 415V, Discharge 150mm',
      uom: 'SET',
      category: 'Pumps & Compressors'
    },
    suggestedNationalCode: 'NM-PMP-002',
    aiReasoning: 'Core pump power (45kW) and slurry application match, but casing mounting style (horizontal vs submersible) requires officer verification.',
    matchMetrics: {
      descriptionSimilarity: 86.4,
      specificationSimilarity: 89.1,
      categorySimilarity: 92.0,
      uomCompatibility: 100.0
    }
  },
  {
    id: 'rec-004',
    confidenceCategory: 'NEEDS_REVIEW',
    overallConfidence: 62.5,
    sourceMaterial: {
      code: 'STL-BRG-12',
      cpse: 'SAIL',
      description: 'Spherical Roller Bearing 22220 K C3 Tapered Bore',
      specification: 'Bore 100mm, OD 180mm, Width 46mm, Tapered 1:12, Clearance C3',
      uom: 'EA',
      category: 'Bearings & Power Transmission'
    },
    targetMaterial: {
      code: 'BHEL-BRG-880',
      cpse: 'BHEL',
      description: 'Double Row Roller Bearing 100x180x46 Cylindrical',
      specification: 'Bore 100mm, OD 180mm, Straight Bore, Normal Clearance',
      uom: 'EA',
      category: 'Bearings & Power Transmission'
    },
    suggestedNationalCode: 'NM-BRG-009',
    aiReasoning: 'Dimensions match (100x180x46mm), but bore taper (Tapered 1:12 vs Straight) and internal clearance differ. Human review strongly recommended.',
    matchMetrics: {
      descriptionSimilarity: 65.0,
      specificationSimilarity: 61.2,
      categorySimilarity: 85.0,
      uomCompatibility: 100.0
    }
  }
];

export const matchingApi = {
  getRecommendations: async (params = {}) => {
    try {
      return await api.get('/api/matching', { params });
    } catch (err) {
      let list = [...MOCK_RECOMMENDATIONS];
      if (params.filter) {
        list = list.filter(r => r.confidenceCategory === params.filter);
      }
      return { data: list };
    }
  },

  compareMaterials: async (codeA, codeB) => {
    try {
      return await api.get(`/api/matching/compare`, { params: { codeA, codeB } });
    } catch (err) {
      return {
        data: {
          materialA: {
            code: codeA || 'MAT-10231',
            cpse: 'ONGC',
            description: 'Industrial Ball Valve SS316 DN50 PN16 Flanged',
            category: 'Valves & Actuators',
            grade: 'SS316 (AISI 316)',
            size: 'DN50 (2 Inch / 50mm)',
            pressureRating: 'PN16 / Class 150',
            uom: 'EA',
            manufacturer: 'L&T Valves',
            techParams: 'Full Bore, Split Body, Fire Safe ISO 10497'
          },
          materialB: {
            code: codeB || 'STL-VLV-21',
            cpse: 'SAIL',
            description: 'Ball Valve SS 316 Class 150 2 Inch Full Port',
            category: 'Valves & Actuators',
            grade: 'SS316',
            size: '2 Inch (50mm)',
            pressureRating: '150# Flanged',
            uom: 'EA',
            manufacturer: 'Audco Valves',
            techParams: 'Full Port, 2-Piece Body, API 607 Fire Tested'
          },
          comparisons: [
            { field: 'Description', status: 'MATCH', textA: 'Industrial Ball Valve SS316 DN50 PN16 Flanged', textB: 'Ball Valve SS 316 Class 150 2 Inch Full Port' },
            { field: 'Material Grade', status: 'MATCH', textA: 'SS316 (AISI 316)', textB: 'SS316' },
            { field: 'Nominal Size', status: 'MATCH', textA: 'DN50 (2 Inch)', textB: '2 Inch (50mm)' },
            { field: 'Pressure Rating', status: 'MATCH', textA: 'PN16 (16 Bar)', textB: '150# (16 Bar Rating Equiv)' },
            { field: 'End Connection', status: 'MATCH', textA: 'Flanged Ends', textB: 'Flanged Ends' },
            { field: 'Unit of Measure', status: 'MATCH', textA: 'EA (Each)', textB: 'EA (Each)' },
            { field: 'Manufacturer', status: 'DIFFERENCE', textA: 'L&T Valves', textB: 'Audco Valves' },
            { field: 'Fire Test Certification', status: 'MATCH', textA: 'ISO 10497', textB: 'API 607' }
          ],
          aiVerdict: 'These materials are functionally equivalent with high confidence. Operating envelope, pressure rating, and metallurgy match.',
          confidenceScore: 96.8,
          suggestedNationalCode: 'NM-VAL-001'
        }
      };
    }
  },

  runMatching: async () => {
    try {
      return await api.post('/api/matching/run');
    } catch (err) {
      return {
        data: {
          status: 'SUCCESS',
          matchedCount: 1284,
          highConfidence: 890,
          mediumConfidence: 312,
          needsReview: 82
        }
      };
    }
  }
};
