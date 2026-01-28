import { useEffect, useState } from 'react';
import { Settings, Sun, Moon, Check, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useSettingsStore } from '@/stores/settingsStore';
import { healthApi } from '@/api/client';

const PROVIDERS = [
    { id: 'openai', name: 'OpenAI', models: ['gpt-4-turbo-preview', 'gpt-4', 'gpt-3.5-turbo'] },
    { id: 'anthropic', name: 'Anthropic', models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'] },
    { id: 'groq', name: 'Groq', models: ['mixtral-8x7b-32768', 'llama2-70b-4096'] },
];

export function SettingsView() {
    const { theme, provider, model, showReasoning, toggleTheme, setProvider, setModel, setShowReasoning } = useSettingsStore();
    const [availableProviders, setAvailableProviders] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function checkHealth() {
            try {
                const health = await healthApi.check();
                setAvailableProviders(health.providers || []);
            } catch (err) {
                console.error('Failed to check health:', err);
            } finally {
                setIsLoading(false);
            }
        }
        checkHealth();
    }, []);


    return (
        <div className="flex-1 flex flex-col h-full">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div>
                    <h1 className="text-xl font-semibold">Settings</h1>
                    <p className="text-sm text-muted-foreground">
                        Configure your CodeGraph experience
                    </p>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-2xl mx-auto space-y-8">
                    {/* Appearance */}
                    <section>
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Settings className="w-5 h-5" />
                            Appearance
                        </h2>

                        <div className="bg-card border border-border rounded-xl p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-medium">Theme</div>
                                    <div className="text-sm text-muted-foreground">
                                        Switch between light and dark mode
                                    </div>
                                </div>
                                <button
                                    onClick={toggleTheme}
                                    className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
                                >
                                    {theme === 'dark' ? (
                                        <>
                                            <Moon className="w-4 h-4" />
                                            Dark
                                        </>
                                    ) : (
                                        <>
                                            <Sun className="w-4 h-4" />
                                            Light
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* LLM Provider */}
                    <section>
                        <h2 className="text-lg font-semibold mb-4">LLM Provider</h2>

                        <div className="bg-card border border-border rounded-xl divide-y divide-border">
                            {PROVIDERS.map((p) => {
                                const isAvailable = availableProviders.includes(p.id);
                                const isSelected = provider === p.id;

                                return (
                                    <div key={p.id} className="p-4">
                                        <div className="flex items-center justify-between mb-3">
                                            <button
                                                onClick={() => isAvailable && setProvider(p.id)}
                                                disabled={!isAvailable}
                                                className={`flex items-center gap-3 ${!isAvailable ? 'opacity-50 cursor-not-allowed' : ''}`}
                                            >
                                                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${isSelected ? 'border-primary bg-primary' : 'border-border'
                                                    }`}>
                                                    {isSelected && <Check className="w-3 h-3 text-primary-foreground" />}
                                                </div>
                                                <span className="font-medium">{p.name}</span>
                                            </button>

                                            {!isAvailable && (
                                                <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
                                                    Not configured
                                                </span>
                                            )}
                                        </div>

                                        {isSelected && (
                                            <div className="ml-8">
                                                <label className="text-sm text-muted-foreground mb-2 block">Model</label>
                                                <select
                                                    value={model}
                                                    onChange={(e) => setModel(e.target.value)}
                                                    className="w-full px-3 py-2 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                                                >
                                                    {p.models.map((m) => (
                                                        <option key={m} value={m}>{m}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {isLoading && (
                            <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Checking available providers...
                            </div>
                        )}
                    </section>

                    {/* Display Options */}
                    <section>
                        <h2 className="text-lg font-semibold mb-4">Display Options</h2>

                        <div className="bg-card border border-border rounded-xl p-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    {showReasoning ? (
                                        <Eye className="w-5 h-5 text-primary" />
                                    ) : (
                                        <EyeOff className="w-5 h-5 text-muted-foreground" />
                                    )}
                                    <div>
                                        <div className="font-medium">Show Reasoning Steps</div>
                                        <div className="text-sm text-muted-foreground">
                                            Display the agent's reasoning process in chat
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setShowReasoning(!showReasoning)}
                                    className={`w-12 h-6 rounded-full transition-colors relative ${showReasoning ? 'bg-primary' : 'bg-secondary'
                                        }`}
                                >
                                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${showReasoning ? 'left-7' : 'left-1'
                                        }`} />
                                </button>
                            </div>
                        </div>
                    </section>

                    {/* About */}
                    <section>
                        <h2 className="text-lg font-semibold mb-4">About</h2>

                        <div className="bg-card border border-border rounded-xl p-4">
                            <div className="text-center">
                                <div className="font-semibold gradient-text text-lg mb-1">CodeGraph</div>
                                <div className="text-sm text-muted-foreground mb-3">Version 0.1.0</div>
                                <p className="text-sm text-muted-foreground">
                                    AI-powered code understanding with graph-based navigation and multi-hop reasoning.
                                </p>
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
