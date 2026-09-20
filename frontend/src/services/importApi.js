import { api } from "./api";

const materialPreviewRow = (row) => ({
  code: row.material_code || "",
  description: row.description || "",
  category: row.category || "-",
  specification:
    typeof row.specifications === "object"
      ? JSON.stringify(row.specifications)
      : row.specifications || "",
  uom: row.unit || "-",
});

const inventoryPreviewRow = (row) => ({
  cpseCode: row.cpse_code || "",
  code: row.material_code || "",
  warehouse: row.warehouse || "",
  available: row.available_quantity ?? "",
  reserved: row.reserved_quantity ?? 0,
  uom: row.unit || "EA",
  unitCost: row.unit_cost ?? "",
  action: row.action || "CREATE",
});

const previewShape = (data, file, importType = "MATERIAL") => {
  const resolvedType = data.import_type || importType;
  return {
    batchId: data.batch_id,
    filename: data.filename || file?.name,
    importType: resolvedType,
    conflictPolicy: data.conflict_policy || "REJECT",
    totalRows: data.total_rows || 0,
    fileSize: file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : "-",
    validRows: data.valid_rows || 0,
    errorRows: data.error_rows || 0,
    warningRows: data.warning_rows || 0,
    validations: [
      {
        type: "success",
        message: `${data.valid_rows || 0} rows passed validation`,
      },
      ...(data.error_rows
        ? [
            {
              type: "error",
              message: `${data.error_rows} rows contain blocking errors and will be skipped`,
            },
          ]
        : []),
      ...(data.warning_rows
        ? [
            {
              type: "warning",
              message: `${data.warning_rows} existing stock rows will be updated`,
            },
          ]
        : []),
    ],
    previewRows: (data.preview || [])
      .slice(0, 5)
      .map(
        resolvedType === "INVENTORY" ? inventoryPreviewRow : materialPreviewRow,
      ),
  };
};

export const importApi = {
  previewFile: async (file, cpseId, options = {}) => {
    const importType = options.importType || "MATERIAL";
    const form = new FormData();
    form.append("file", file);
    form.append("cpse_id", String(cpseId));
    form.append("import_type", importType);
    form.append("conflict_policy", options.conflictPolicy || "REJECT");
    const response = await api.post("/api/imports/preview", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return { data: previewShape(response.data, file, importType) };
  },
  validateFile: async (file, cpseId, options = {}) =>
    importApi.previewFile(file, cpseId, options),
  startImport: async ({ batchId }) => {
    const response = await api.post(`/api/imports/${batchId}/queue`, null, {
      headers: { "Idempotency-Key": `import-${batchId}` },
    });
    return {
      data: {
        jobId: response.data.id,
        batchId: response.data.id,
        status: response.data.status,
        totalRows: response.data.total_rows,
      },
    };
  },
  retryAi: async (batchId) => {
    const response = await api.post(`/api/imports/${batchId}/queue`, null, {
      headers: {
        "Idempotency-Key": `import-${batchId}-ai-retry-${Date.now()}`,
      },
    });
    return {
      data: {
        jobId: response.data.id,
        batchId: response.data.id,
        status: response.data.status,
        totalRows: response.data.total_rows,
      },
    };
  },
  getImportProgress: async (jobId) => {
    const response = await api.get(`/api/imports/${jobId}/status`);
    const batch = response.data || {};
    const successful = batch.successful_rows || 0;
    const failed = batch.failed_rows || 0;
    return {
      data: {
        jobId,
        importType: batch.import_type || "MATERIAL",
        progress: batch.progress_percent || 0,
        processedRows: batch.processed_rows || 0,
        totalRows: batch.total_rows || 0,
        stage: batch.current_stage || "QUEUED",
        stageMessage: batch.status?.startsWith("COMPLETED")
          ? `Import completed: ${successful} successful, ${failed} failed.`
          : batch.error_message ||
            `Import ${String(batch.status || "queued").toLowerCase()}…`,
        status: batch.status || "QUEUED",
      },
    };
  },
  getImportBatches: async () => {
    const response = await api.get("/api/imports");
    return {
      data: (response.data || []).map((batch) => ({
        ...batch,
        importType: batch.import_type || "MATERIAL",
        totalRecords: batch.total_rows,
        successCount: batch.successful_rows,
        errorCount: batch.failed_rows,
        importedAt: batch.created_at?.replace("T", " ").slice(0, 16) || "",
      })),
    };
  },
  getImportErrors: (id) => api.get(`/api/imports/${id}/errors`),
};
