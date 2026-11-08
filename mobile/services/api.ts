import { Alert } from 'react-native';
import { COLORS, API_BASE_URL } from '@/constants/colors';

const API = API_BASE_URL;

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const url = `${API}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    const body = await res.text();
    let data: any = null;
    if (body) {
      try {
        data = JSON.parse(body);
      } catch {
        data = body;
      }
    }
    if (!res.ok) {
      throw new Error(data?.message || `Request failed (${res.status})`);
    }
    return data;
  } catch (err: any) {
    console.error('API error:', path, err);
    throw err;
  }
}

export const api = {
  health: () => request('/api/health'),

  uploadScan: async (files: { uri: string; name: string; type: string }[]) => {
    const form = new FormData();
    for (const file of files) {
      form.append('files', {
        uri: file.uri,
        name: file.name,
        type: file.type,
      } as any);
    }
    return request('/api/scan/upload', {
      method: 'POST',
      body: form,
      headers: {}, // let fetch set multipart boundary
    });
  },

  processScan: async (scanId: string, language: string) => {
    return request('/api/scan/process', {
      method: 'POST',
      body: JSON.stringify({ scan_id: scanId, language }),
    });
  },

  getScan: (scanId: string) => request(`/api/scan/${scanId}`),

  getFullReport: (scanId: string) => request(`/api/scan/report/${scanId}`),

  translateReport: async (scanId: string, targetLanguage: string) => {
    return request(
      `/api/scan/translate/report?scan_id=${encodeURIComponent(scanId)}&target_language=${encodeURIComponent(targetLanguage)}`,
      { method: 'POST' }
    );
  },

  getHistory: () => request('/api/scan/history'),

  deleteScan: (scanId: string) => request(`/api/scan/${scanId}`, { method: 'DELETE' }),

  translate: async (text: string, targetLanguage: string, sourceLanguage = 'en') => {
    return request('/api/translate', {
      method: 'POST',
      body: JSON.stringify({ text, target_language: targetLanguage, source_language: sourceLanguage }),
    });
  },

  compare: async (scanIdA: string, scanIdB: string) => {
    return request('/api/compare', {
      method: 'POST',
      body: JSON.stringify({ scan_id_a: scanIdA, scan_id_b: scanIdB }),
    });
  },

  getIngredient: (ingredientId: string) => request(`/api/ingredients/${ingredientId}`),
};
