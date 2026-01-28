import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
    theme: 'light' | 'dark';
    provider: string;
    model: string;
    showReasoning: boolean;
    toggleTheme: () => void;
    setProvider: (provider: string) => void;
    setModel: (model: string) => void;
    setShowReasoning: (show: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
    persist(
        (set) => ({
            theme: 'dark',
            provider: 'openai',
            model: 'gpt-4-turbo-preview',
            showReasoning: true,

            toggleTheme: () =>
                set((state) => {
                    const newTheme = state.theme === 'dark' ? 'light' : 'dark';
                    document.documentElement.classList.toggle('dark', newTheme === 'dark');
                    return { theme: newTheme };
                }),

            setProvider: (provider) => set({ provider }),
            setModel: (model) => set({ model }),
            setShowReasoning: (showReasoning) => set({ showReasoning }),
        }),
        {
            name: 'codegraph-settings',
        }
    )
);
