// API Types

export interface Repository {
    id: string;
    url: string;
    name: string;
    branch: string;
    status: 'pending' | 'cloning' | 'indexing' | 'ready' | 'error';
    file_count?: number;
    node_count?: number;
    created_at: string;
    indexed_at?: string;
    error_message?: string;
}

export interface Citation {
    file_path: string;
    start_line: number;
    end_line: number;
    content: string;
    node_type?: string;
    node_name?: string;
}

export interface ReasoningStep {
    step_number: number;
    action: string;
    node_visited?: string;
    observation?: string;
}

export interface QueryResponse {
    answer: string;
    citations: Citation[];
    reasoning_steps: ReasoningStep[];
    confidence: number;
    tokens_used?: number;
    processing_time_ms?: number;
}

export interface GraphNode {
    id: string;
    type: string;
    name: string;
    file_path: string;
    start_line: number;
    end_line: number;
    signature?: string;
    docstring?: string;
    metadata?: Record<string, unknown>;
}

export interface GraphEdge {
    source: string;
    target: string;
    type: string;
    metadata?: Record<string, unknown>;
}

export interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
    stats?: Record<string, number>;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    citations?: Citation[];
    reasoning_steps?: ReasoningStep[];
    timestamp: Date;
}
