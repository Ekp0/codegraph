import { create } from 'zustand';
import type { ChatMessage, QueryResponse } from '@/types';

interface ChatState {
    messages: ChatMessage[];
    isLoading: boolean;
    error: string | null;
    addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    clearMessages: () => void;
    updateLastAssistantMessage: (response: QueryResponse) => void;
}

export const useChatStore = create<ChatState>((set) => ({
    messages: [],
    isLoading: false,
    error: null,

    addMessage: (message) =>
        set((state) => ({
            messages: [
                ...state.messages,
                {
                    ...message,
                    id: crypto.randomUUID(),
                    timestamp: new Date(),
                },
            ],
        })),

    setLoading: (isLoading) => set({ isLoading }),

    setError: (error) => set({ error }),

    clearMessages: () => set({ messages: [], error: null }),

    updateLastAssistantMessage: (response) =>
        set((state) => {
            const messages = [...state.messages];
            const lastIdx = messages.length - 1;
            if (lastIdx >= 0 && messages[lastIdx].role === 'assistant') {
                messages[lastIdx] = {
                    ...messages[lastIdx],
                    content: response.answer,
                    citations: response.citations,
                    reasoning_steps: response.reasoning_steps,
                };
            }
            return { messages };
        }),
}));
