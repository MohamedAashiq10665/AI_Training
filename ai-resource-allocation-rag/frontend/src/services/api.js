import axios from "axios";

const defaultApiBaseUrl =
  typeof window !== "undefined"
    ? `http://${window.location.hostname}:8000`
    : "http://localhost:8000";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl,
});

const TOKEN_KEY = "resource_ai_access_token";
const USER_ROLE_KEY = "resource_ai_user_role";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredRole() {
  return localStorage.getItem(USER_ROLE_KEY);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_ROLE_KEY);
  delete api.defaults.headers.common.Authorization;
}

export function applyToken(token) {
  api.defaults.headers.common.Authorization = `Bearer ${token}`;
}

export async function login(username, password) {
  const response = await api.post("/auth/login", { username, password });
  const token = response?.data?.access_token;
  const role = response?.data?.role || "viewer";

  if (!token) {
    throw new Error("Authentication failed: missing access token.");
  }

  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_ROLE_KEY, role);
  applyToken(token);
  return { token, role };
}

async function ensureAuth() {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Not authenticated. Please log in.");
  }
  applyToken(token);
}

async function withAuth(call) {
  await ensureAuth();
  try {
    return await call();
  } catch (error) {
    if (error?.response?.status === 401) {
      clearSession();
      throw new Error("Your session expired. Please log in again.");
    }
    throw error;
  }
}

export const getAnalytics = async () => (await withAuth(() => api.get("/analytics"))).data;
export const getBench = async () => (await withAuth(() => api.get("/bench"))).data;
export const getUtilization = async () => (await withAuth(() => api.get("/utilization"))).data;
export const getEmployees = async (limit = 500) =>
  (await withAuth(() => api.get("/employees", { params: { limit } }))).data;
export const getProjectTeams = async () => (await withAuth(() => api.get("/project-teams"))).data;
export const getProjects = async (limit = 500) =>
  (await withAuth(() => api.get("/projects", { params: { limit } }))).data;
export const getProjectDetails = async (projectId) =>
  (await withAuth(() => api.get(`/projects/${projectId}/details`))).data;
export const assignEmployeeToProject = async (projectId, payload) =>
  (await withAuth(() => api.post(`/projects/${projectId}/assign`, payload))).data;
export const unassignEmployeeFromProject = async (projectId, payload) =>
  (await withAuth(() => api.post(`/projects/${projectId}/unassign`, payload))).data;
export const getProjectAiRecommendations = async (projectId, payload) =>
  (await withAuth(() => api.post(`/projects/${projectId}/ai-recommend-chat`, payload))).data;

export const createIntentAssignProposal = async (projectId, payload) =>
  (await withAuth(() => api.post(`/projects/${projectId}/intent-driver/propose`, payload))).data;

export const confirmIntentAssignProposal = async (projectId, payload) =>
  (await withAuth(() => api.post(`/projects/${projectId}/intent-driver/confirm`, payload))).data;

export const getRecommendations = async (payload) =>
  (await withAuth(() => api.post("/recommend", payload))).data;

export default api;
