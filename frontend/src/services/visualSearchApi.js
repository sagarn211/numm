import { api } from "./api";
export const visualSearchApi = {
  search: (file, topK = 5) => {
    const form = new FormData();
    form.append("file", file);
    form.append("top_k", String(topK));
    return api.post("/api/visual-search", form);
  },
};
