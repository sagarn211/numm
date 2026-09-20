import { api } from "./api";

export const notificationApi = {
  list: () => api.get("/api/notifications"),
  unreadCount: () => api.get("/api/notifications/unread-count"),
  markRead: (id) => api.patch(`/api/notifications/${id}/read`),
  markAllRead: () => api.post("/api/notifications/mark-all-read"),
};
