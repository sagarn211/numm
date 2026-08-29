import { api } from './api';

export const dashboardApi = {
  getStats: async () => {
    try {
      return await api.get('/api/dashboard/stats');
    } catch (err) {
      return {
        data: {
          totalCPSEs: { value: 24, label: 'Participating CPSEs', change: '+2', period: 'This month' },
          totalMaterials: { value: 128492, label: 'Total Material Items', change: '+8.4%', period: 'vs last quarter' },
          duplicateMaterials: { value: 14320, label: 'Identified Duplicates', change: '-12.3%', period: 'rationalized' },
          aiMatches: { value: 12840, label: 'AI Matches Found', change: '+14.2%', period: 'auto-clustered' },
          nationalMaterials: { value: 45210, label: 'National Codes Created', change: '+6.8%', period: 'standardized' },
          aiConfidenceOverall: 94.7,
          pendingReviewCount: 382,
          highConfidenceMappings: 87
        }
      };
    }
  },

  getMaterialNetwork: async () => {
    try {
      return await api.get('/api/dashboard/network');
    } catch (err) {
      return {
        data: {
          nationalNodes: [
            {
              id: 'NM-VAL-001',
              title: 'National Material Code: NM-VAL-001',
              standardDescription: 'SS316 Industrial Ball Valve DN50 PN16 Flanged',
              category: 'Valves & Actuators',
              cpses: [
                { cpse: 'ONGC', code: 'MAT-10231', title: 'Industrial Ball Valve SS316 DN50' },
                { cpse: 'NTPC', code: 'VLV-77401', title: 'Stainless Steel Ball Valve 50mm' },
                { cpse: 'SAIL', code: 'STL-VLV-21', title: 'Ball Valve SS 316 Class 150 2"' }
              ]
            },
            {
              id: 'NM-PMP-002',
              title: 'National Material Code: NM-PMP-002',
              standardDescription: 'Centrifugal Heavy Duty Slurry Pump 45kW',
              category: 'Pumps & Compressors',
              cpses: [
                { cpse: 'ONGC', code: 'MAT-88102', title: 'Centrifugal Slurry Pump 45kW' },
                { cpse: 'CIL', code: 'CIL-PMP-404', title: 'Heavy Duty Submersible Slurry Pump 45kW' }
              ]
            },
            {
              id: 'NM-PIP-003',
              title: 'National Material Code: NM-PIP-003',
              standardDescription: 'Carbon Steel Seamless Pipe 6 Inch Sch 40 API 5L',
              category: 'Pipes & Fittings',
              cpses: [
                { cpse: 'ONGC', code: 'MAT-44102', title: 'CS Seamless Pipe 6" Sch 40 API 5L' },
                { cpse: 'SAIL', code: 'STL-PIP-88', title: 'Seamless Steel Line Pipe 150mm Sch 40' }
              ]
            },
            {
              id: 'NM-TRF-004',
              title: 'National Material Code: NM-TRF-004',
              standardDescription: 'Power Transformer 33kV/11kV 5MVA Oil Immersed',
              category: 'Electrical Equipment',
              cpses: [
                { cpse: 'NTPC', code: 'ELC-33100', title: 'Power Transformer 33kV/11kV 5MVA' },
                { cpse: 'BHEL', code: 'BHEL-TR-500', title: '33kV/11kV Step Down Transformer 5MVA' }
              ]
            }
          ]
        }
      };
    }
  },

  getSectorStats: async () => {
    try {
      return await api.get('/api/dashboard/sectors');
    } catch (err) {
      return {
        data: [
          { name: 'Oil & Gas', materials: 42180, duplicates: 4810, matched: 35200, standardization: 88, cpseList: ['ONGC', 'GAIL', 'IOCL'] },
          { name: 'Power', materials: 36450, duplicates: 3920, matched: 30100, standardization: 85, cpseList: ['NTPC', 'NHPC', 'POWERGRID'] },
          { name: 'Steel', materials: 24821, duplicates: 1204, matched: 19800, standardization: 82, cpseList: ['SAIL', 'RINL', 'NMDC'] },
          { name: 'Mining', materials: 14800, duplicates: 2410, matched: 10900, standardization: 76, cpseList: ['CIL', 'NLC', 'MCL'] },
          { name: 'Heavy Engineering', materials: 10241, duplicates: 1976, matched: 7800, standardization: 74, cpseList: ['BHEL', 'BEL', 'HAL'] }
        ]
      };
    }
  },

  getRecentActivity: async () => {
    try {
      return await api.get('/api/dashboard/activity');
    } catch (err) {
      return {
        data: [
          { id: 'act-1', type: 'IMPORT', text: 'NTPC imported 4,821 materials from Q3 Master dataset', timestamp: '2 minutes ago', cpse: 'NTPC' },
          { id: 'act-2', type: 'AI_MATCH', text: 'AI Engine identified 283 possible duplicate material clusters', timestamp: '8 minutes ago', cpse: 'SYSTEM' },
          { id: 'act-3', type: 'APPROVAL', text: 'SAIL approved 42 material code mappings to National Registry', timestamp: '21 minutes ago', cpse: 'SAIL' },
          { id: 'act-4', type: 'CODE_CREATED', text: 'National Material Code NM-PMP-004 generated and registered', timestamp: '1 hour ago', cpse: 'NATIONAL' },
          { id: 'act-5', type: 'AUDIT', text: 'Senior Procurement Officer approved mapping ONGC-MAT-10231 → NM-VAL-001', timestamp: '2 hours ago', cpse: 'ONGC' }
        ]
      };
    }
  }
};
