import { User, Bot, FileCode, ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { useState } from 'react';
import type { ChatMessage as ChatMessageType, Citation, ReasoningStep } from '@/types';
import { useSettingsStore } from '@/stores/settingsStore';

interface ChatMessageProps {
    message: ChatMessageType;
    isLoading?: boolean;
}

export function ChatMessage({ message, isLoading }: ChatMessageProps) {
    const [showReasoning, setShowReasoning] = useState(false);
    const { showReasoning: defaultShowReasoning } = useSettingsStore();

    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${isUser
                    ? 'bg-primary/10 text-primary'
                    : 'bg-gradient-to-br from-purple-500/20 to-primary/20 text-purple-400'
                }`}>
                {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
            </div>

            {/* Content */}
            <div className={`flex-1 space-y-3 ${isUser ? 'text-right' : ''}`}>
                {/* Message body */}
                <div className={`inline-block p-4 rounded-2xl max-w-full ${isUser
                        ? 'bg-primary text-primary-foreground rounded-tr-sm'
                        : 'bg-secondary/50 rounded-tl-sm'
                    }`}>
                    {isLoading && !message.content ? (
                        <div className="flex items-center gap-2 text-muted-foreground">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Thinking...</span>
                        </div>
                    ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none text-left whitespace-pre-wrap">
                            {message.content}
                        </div>
                    )}
                </div>

                {/* Reasoning steps (assistant only) */}
                {!isUser && message.reasoning_steps && message.reasoning_steps.length > 0 && (
                    <div className="text-left">
                        <button
                            onClick={() => setShowReasoning(!showReasoning)}
                            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                        >
                            {showReasoning ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            {message.reasoning_steps.length} reasoning steps
                        </button>

                        {(showReasoning || defaultShowReasoning) && (
                            <div className="mt-2 pl-4 border-l-2 border-border space-y-2">
                                {message.reasoning_steps.map((step, idx) => (
                                    <ReasoningStepCard key={idx} step={step} />
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Citations (assistant only) */}
                {!isUser && message.citations && message.citations.length > 0 && (
                    <div className="text-left">
                        <div className="text-xs text-muted-foreground mb-2">
                            {message.citations.length} citation{message.citations.length > 1 ? 's' : ''}
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {message.citations.map((citation, idx) => (
                                <CitationCard key={idx} citation={citation} index={idx + 1} />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function ReasoningStepCard({ step }: { step: ReasoningStep }) {
    return (
        <div className="text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Step {step.step_number}:</span>{' '}
            {step.action}
            {step.node_visited && (
                <span className="ml-1 text-primary">→ {step.node_visited}</span>
            )}
        </div>
    );
}

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
    const [isExpanded, setIsExpanded] = useState(false);

    const fileName = citation.file_path.split('/').pop() || citation.file_path;

    return (
        <div className="bg-secondary/30 rounded-lg border border-border overflow-hidden">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 px-3 py-2 hover:bg-secondary/50 transition-colors w-full text-left"
            >
                <FileCode className="w-4 h-4 text-primary flex-shrink-0" />
                <span className="text-sm font-medium truncate">{fileName}</span>
                <span className="text-xs text-muted-foreground">
                    L{citation.start_line}-{citation.end_line}
                </span>
                <span className="ml-auto text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                    [{index}]
                </span>
            </button>

            {isExpanded && (
                <div className="border-t border-border">
                    <pre className="p-3 text-xs overflow-x-auto bg-background/50">
                        <code>{citation.content}</code>
                    </pre>
                </div>
            )}
        </div>
    );
}
