import axios from "axios";
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";
export const api = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("numm_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(
  (r) => r,
  (e) => {
    if (e.response?.status === 401) {
      const hadSession = !!localStorage.getItem("numm_token");
      localStorage.removeItem("numm_token");
      localStorage.removeItem("numm_user");
      if (hadSession) {
        sessionStorage.setItem(
          "numm_session_message",
          "Your session expired. Please sign in again.",
        );
        window.dispatchEvent(new Event("numm:session-expired"));
      }
    }
    return Promise.reject(e);
  },
);
