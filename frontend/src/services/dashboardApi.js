import { api } from './api';

const stat = (v, label) => ({ value: Number(v || 0), label, change: 'Live', period: 'PostgreSQL' });

export const dashboardApi = {
  getStats: async () => {
    const { data: d } = await api.get('/api/dashboard/stats');
    return {
      data: {
        totalCPSEs: stat(d.total_cpses ?? d.participating_cpses, 'Participating CPSEs'),
        totalMaterials: stat(d.total_materials ?? d.total_legacy_materials, 'Total Material Items'),
        duplicateMaterials: stat(d.duplicate_candidate_materials ?? d.pending_matches, `${d.duplicate_risk_percent ?? 0}% duplicate risk`),
        aiMatches: stat(d.mapped_materials, 'Mapped Materials'),
        nationalMaterials: stat(d.total_national_materials ?? d.national_materials, 'National Codes Created'),
        aiConfidenceOverall: 0,
        pendingReviewCount: d.pending_matches ?? 0,
        highConfidenceMappings: d.mapped_materials ?? 0,
        crossCpseInventory: d.cross_cpse_inventory ?? 0,
        materialRequests: d.material_requests ?? 0,
        duplicateRiskPercent: d.duplicate_risk_percent ?? 0,
        mappingCoveragePercent: d.mapping_coverage_percent ?? 0,
        estimatedSavingsOpportunity: d.estimated_savings_opportunity ?? 0,
        stockAnalytics: d.stock_analytics,
        excessInventoryQuantity: d.excess_inventory_quantity ?? 0,
        approvalTurnaroundHours: d.average_approval_turnaround_hours ?? 0,
        importErrorRatePercent: d.import_error_rate_percent ?? 0,
        savingsAssumption: d.savings_assumption || '',
        harmonization: d.harmonization || null,
      }
    };
  },

  getMaterialNetwork: async () => {
    const natRes = await api.get('/api/national-materials');
    const nationals = natRes.data || [];

    // Fetch individual national detail with mappings
    const detailedNodes = await Promise.all(
      nationals.slice(0, 5).map(async (n) => {
        const detailRes = await api.get(`/api/national-materials/${n.id}/360`);
        const linkedCpses = (detailRes.data?.legacy_mappings || []).map(m => ({
          cpse: m.cpse_code,
          code: m.material.material_code,
          title: m.material.description,
        }));
        return {
          id: n.national_code,
          title: n.description,
          standardDescription: n.description,
          category: n.category || 'General',
          cpses: linkedCpses
        };
      })
    );

    return { data: { nationalNodes: detailedNodes } };
  },

  getSectorStats: async () => {
    const response = await api.get('/api/dashboard/analytics');
    return { data: response.data?.sectors || [] };
  },

  getRecentActivity: async () => {
    const r = await api.get('/api/audit');
    return {
      data: (r.data || []).slice(0, 8).map(x => {
        const details = typeof x.details === 'object' && x.details ? x.details : {};
        const msg = details.message || `${x.action} event on ${x.entity_type || 'Entity'} #${x.entity_id ?? ''}`;
        return {
          id: x.id,
          type: x.action,
          text: msg,
          timestamp: x.created_at?.replace('T', ' ').slice(0, 16) || '',
          cpse: details.cpse || 'SYSTEM'
        };
      })
    };
  },
};
