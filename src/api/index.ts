import type { UserProfile, ProfileResponse, AnalyzeResult, HistoryRecord } from '../types';

// Vercel 部署时前后端同域，直接用相对路径
const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  async saveProfile(profile: UserProfile): Promise<ProfileResponse> {
    return request(`${BASE}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
  },

  async analyzeMenu(
    image: File,
    userId: string,
    mood: string
  ): Promise<AnalyzeResult> {
    const form = new FormData();
    form.append('image', image);
    form.append('user_id', userId);
    form.append('mood', mood);
    return request(`${BASE}/analyze-menu`, { method: 'POST', body: form });
  },

  async getHistory(userId?: string): Promise<{ history: HistoryRecord[]; total: number }> {
    const url = userId ? `${BASE}/history?user_id=${userId}` : `${BASE}/history`;
    return request(url);
  },

  async healthz(): Promise<{ status: string; mock_mode: boolean }> {
    return request(`${BASE}/healthz`);
  },
};
