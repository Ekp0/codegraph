import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useRepoStore } from '@/stores/repoStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { queryApi } from '@/api/client';
import { ChatMessage } from './ChatMessage';

export function ChatView() {
    const [input, setInput] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const { messages, isLoading, error, addMessage, setLoading, setError, updateLastAssistantMessage } = useChatStore();
    const { selectedRepo } = useRepoStore();
    const { provider, model } = useSettingsStore();

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
        }
    }, [input]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !selectedRepo) return;

        const question = input.trim();
        setInput('');
        setError(null);

        // Add user message
        addMessage({ role: 'user', content: question });

        // Add placeholder assistant message
        addMessage({ role: 'assistant', content: '' });

        setLoading(true);

        try {
            const response = await queryApi.ask(selectedRepo.id, question);
            updateLastAssistantMessage(response);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to get response');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-full">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div>
                    <h1 className="text-xl font-semibold">Chat</h1>
                    <p className="text-sm text-muted-foreground">
                        {selectedRepo ? `Ask questions about ${selectedRepo.name}` : 'Select a repository to start'}
                    </p>
                </div>
                {selectedRepo && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-secondary/50 rounded-full text-sm">
                        <span className="text-muted-foreground">Using:</span>
                        <span className="font-medium">{provider}/{model}</span>
                    </div>
                )}
            </header>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center mb-4">
                            <Sparkles className="w-8 h-8 text-primary" />
                        </div>
                        <h2 className="text-xl font-semibold mb-2">Ask anything about the code</h2>
                        <p className="text-muted-foreground max-w-md">
                            {selectedRepo
                                ? "I'll navigate through the codebase, follow function calls, and provide answers with citations."
                                : "Select a repository from the sidebar to get started."
                            }
                        </p>
                        {selectedRepo && (
                            <div className="mt-6 flex flex-wrap gap-2 justify-center">
                                {[
                                    "How does authentication work?",
                                    "What are the main API endpoints?",
                                    "Explain the data models",
                                ].map((suggestion) => (
                                    <button
                                        key={suggestion}
                                        onClick={() => setInput(suggestion)}
                                        className="px-3 py-1.5 bg-secondary/50 hover:bg-secondary rounded-full text-sm transition-colors"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="max-w-3xl mx-auto space-y-6">
                        {messages.map((message) => (
                            <ChatMessage key={message.id} message={message} isLoading={isLoading && message === messages[messages.length - 1] && message.role === 'assistant'} />
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Error banner */}
            {error && (
                <div className="mx-6 mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-sm text-destructive">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                </div>
            )}

            {/* Input */}
            <div className="p-6 pt-0">
                <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
                    <div className="relative bg-secondary/30 rounded-xl border border-border focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={selectedRepo ? "Ask a question about the code..." : "Select a repository first"}
                            disabled={!selectedRepo}
                            rows={1}
                            className="w-full px-4 py-3 pr-12 bg-transparent resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading || !selectedRepo}
                            className="absolute right-2 bottom-2 p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
