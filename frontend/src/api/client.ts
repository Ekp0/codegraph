const API_BASE = '/api';

class ApiClient {
    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${API_BASE}${endpoint}`;

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `API error: ${response.status}`);
        }

        return response.json();
    }

    async get<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: 'GET' });
    }

    async post<T>(endpoint: string, data?: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined,
        });
    }

    async delete<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: 'DELETE' });
    }
}

export const apiClient = new ApiClient();

// Repository API
export const repositoryApi = {
    list: () => apiClient.get<{ repositories: Repository[]; total: number }>('/repositories'),
    get: (id: string) => apiClient.get<Repository>(`/repositories/${id}`),
    create: (url: string, branch = 'main') =>
        apiClient.post<Repository>('/repositories', { url, branch }),
    delete: (id: string) => apiClient.delete(`/repositories/${id}`),
};

// Query API
export const queryApi = {
    ask: (repositoryId: string, question: string) =>
        apiClient.post<QueryResponse>('/queries', { repository_id: repositoryId, question }),
};

// Graph API
export const graphApi = {
    get: (repositoryId: string) =>
        apiClient.get<GraphData>(`/graph/${repositoryId}`),
    getNode: (repositoryId: string, nodeId: string) =>
        apiClient.get<GraphNode>(`/graph/${repositoryId}/node/${nodeId}`),
    getNeighbors: (repositoryId: string, nodeId: string, depth = 1) =>
        apiClient.get<GraphData>(`/graph/${repositoryId}/neighbors/${nodeId}?depth=${depth}`),
};

// Health API
export const healthApi = {
    check: () => apiClient.get<{ status: string; providers: string[] }>('/health'),
};

import { Repository, QueryResponse, GraphData, GraphNode } from '@/types';
