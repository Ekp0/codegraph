import { create } from 'zustand';
import type { Repository } from '@/types';

interface RepoState {
    repositories: Repository[];
    selectedRepo: Repository | null;
    isLoading: boolean;
    error: string | null;
    setRepositories: (repos: Repository[]) => void;
    addRepository: (repo: Repository) => void;
    selectRepo: (repo: Repository | null) => void;
    updateRepository: (id: string, updates: Partial<Repository>) => void;
    removeRepository: (id: string) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
}

export const useRepoStore = create<RepoState>((set) => ({
    repositories: [],
    selectedRepo: null,
    isLoading: false,
    error: null,

    setRepositories: (repositories) => set({ repositories }),

    addRepository: (repo) =>
        set((state) => ({
            repositories: [...state.repositories, repo],
        })),

    selectRepo: (selectedRepo) => set({ selectedRepo }),

    updateRepository: (id, updates) =>
        set((state) => ({
            repositories: state.repositories.map((r) =>
                r.id === id ? { ...r, ...updates } : r
            ),
            selectedRepo:
                state.selectedRepo?.id === id
                    ? { ...state.selectedRepo, ...updates }
                    : state.selectedRepo,
        })),

    removeRepository: (id) =>
        set((state) => ({
            repositories: state.repositories.filter((r) => r.id !== id),
            selectedRepo: state.selectedRepo?.id === id ? null : state.selectedRepo,
        })),

    setLoading: (isLoading) => set({ isLoading }),
    setError: (error) => set({ error }),
}));
