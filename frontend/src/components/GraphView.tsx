import { useEffect, useCallback, useState } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    MarkerType,
    BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useRepoStore } from '@/stores/repoStore';
import { graphApi } from '@/api/client';
import { Loader2, Network } from 'lucide-react';
import type { GraphNode, GraphEdge } from '@/types';

const nodeColors: Record<string, string> = {
    module: '#3b82f6',   // blue
    class: '#8b5cf6',    // purple
    function: '#10b981', // green
    method: '#14b8a6',   // teal
    variable: '#f59e0b', // amber
    import: '#6b7280',   // gray
};

function transformToReactFlow(graphData: { nodes: GraphNode[]; edges: GraphEdge[] }) {
    // Calculate layout positions (simple grid for now)
    const nodesByType: Record<string, GraphNode[]> = {};
    graphData.nodes.forEach(node => {
        const type = node.type;
        if (!nodesByType[type]) nodesByType[type] = [];
        nodesByType[type].push(node);
    });

    const nodes: Node[] = [];
    let yOffset = 0;

    Object.entries(nodesByType).forEach(([type, typeNodes]) => {
        typeNodes.forEach((node, idx) => {
            nodes.push({
                id: node.id,
                position: { x: (idx % 4) * 250, y: yOffset + Math.floor(idx / 4) * 120 },
                data: {
                    label: (
                        <div className="text-left">
                            <div className="font-semibold truncate">{node.name}</div>
                            <div className="text-xs opacity-75">{node.type}</div>
                        </div>
                    ),
                    ...node,
                },
                style: {
                    background: `${nodeColors[type] || '#6b7280'}15`,
                    border: `2px solid ${nodeColors[type] || '#6b7280'}`,
                    borderRadius: 8,
                    padding: 10,
                    minWidth: 150,
                },
            });
        });
        yOffset += Math.ceil(typeNodes.length / 4) * 120 + 80;
    });

    const edges: Edge[] = graphData.edges.map((edge, idx) => ({
        id: `e-${idx}`,
        source: edge.source,
        target: edge.target,
        label: edge.type,
        type: 'smoothstep',
        animated: edge.type === 'calls',
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#6b728050' },
        labelStyle: { fontSize: 10, fill: '#6b7280' },
    }));

    return { nodes, edges };
}

export function GraphView() {
    const { selectedRepo } = useRepoStore();
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [stats, setStats] = useState<Record<string, number>>({});

    const fetchGraph = useCallback(async () => {
        if (!selectedRepo || selectedRepo.status !== 'ready') return;

        setIsLoading(true);
        setError(null);

        try {
            const graphData = await graphApi.get(selectedRepo.id);
            const { nodes: rfNodes, edges: rfEdges } = transformToReactFlow(graphData);
            setNodes(rfNodes);
            setEdges(rfEdges);
            setStats(graphData.stats || {
                nodes: graphData.nodes.length,
                edges: graphData.edges.length,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load graph');
        } finally {
            setIsLoading(false);
        }
    }, [selectedRepo, setNodes, setEdges]);

    useEffect(() => {
        fetchGraph();
    }, [fetchGraph]);

    if (!selectedRepo) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center mb-4">
                    <Network className="w-8 h-8 text-primary" />
                </div>
                <h2 className="text-xl font-semibold mb-2">Code Graph Visualization</h2>
                <p className="text-muted-foreground max-w-md">
                    Select a repository to visualize its code structure and relationships.
                </p>
            </div>
        );
    }

    if (selectedRepo.status !== 'ready') {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
                <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
                <p className="text-muted-foreground">
                    Waiting for repository indexing to complete...
                </p>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col h-full">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 border-b border-border">
                <div>
                    <h1 className="text-xl font-semibold">Graph</h1>
                    <p className="text-sm text-muted-foreground">
                        Visualize code relationships in {selectedRepo.name}
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    {Object.entries(stats).map(([key, value]) => (
                        <div key={key} className="text-center">
                            <div className="text-lg font-semibold">{value}</div>
                            <div className="text-xs text-muted-foreground capitalize">{key}</div>
                        </div>
                    ))}
                </div>
            </header>

            {/* Graph */}
            <div className="flex-1 relative">
                {isLoading && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80">
                        <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    </div>
                )}

                {error && (
                    <div className="absolute inset-0 z-10 flex items-center justify-center">
                        <div className="text-center">
                            <p className="text-destructive mb-2">{error}</p>
                            <button
                                onClick={fetchGraph}
                                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                )}

                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    fitView
                    attributionPosition="bottom-right"
                    proOptions={{ hideAttribution: true }}
                >
                    <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
                    <Controls />
                </ReactFlow>

                {/* Legend */}
                <div className="absolute bottom-4 left-4 bg-card/90 backdrop-blur-sm border border-border rounded-lg p-3">
                    <div className="text-xs font-medium mb-2">Node Types</div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                        {Object.entries(nodeColors).map(([type, color]) => (
                            <div key={type} className="flex items-center gap-2 text-xs">
                                <div
                                    className="w-3 h-3 rounded"
                                    style={{ backgroundColor: color }}
                                />
                                <span className="capitalize">{type}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
