import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, GitBranch, Network, Settings, Plus, ChevronDown, Check, Loader2, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { useRepoStore } from '@/stores/repoStore';
import { AddRepoDialog } from './AddRepoDialog';
import type { Repository } from '@/types';

const navItems = [
    { path: '/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/graph', icon: Network, label: 'Graph' },
    { path: '/settings', icon: Settings, label: 'Settings' },
];

function getStatusIcon(status: Repository['status']) {
    switch (status) {
        case 'ready':
            return <Check className="w-3 h-3 text-green-500" />;
        case 'pending':
        case 'cloning':
        case 'indexing':
            return <Loader2 className="w-3 h-3 text-yellow-500 animate-spin" />;
        case 'error':
            return <AlertCircle className="w-3 h-3 text-red-500" />;
    }
}

export function Sidebar() {
    const location = useLocation();
    const [showRepoDropdown, setShowRepoDropdown] = useState(false);
    const [showAddDialog, setShowAddDialog] = useState(false);

    const { repositories, selectedRepo, selectRepo } = useRepoStore();

    return (
        <>
            <aside className="w-64 bg-card border-r border-border flex flex-col">
                {/* Logo */}
                <div className="p-4 border-b border-border">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center">
                            <GitBranch className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-semibold text-lg gradient-text">CodeGraph</span>
                    </div>
                </div>

                {/* Repository Selector */}
                <div className="p-3 border-b border-border">
                    <div className="relative">
                        <button
                            onClick={() => setShowRepoDropdown(!showRepoDropdown)}
                            className="w-full flex items-center justify-between p-2 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors text-sm"
                        >
                            <div className="flex items-center gap-2 truncate">
                                {selectedRepo ? (
                                    <>
                                        {getStatusIcon(selectedRepo.status)}
                                        <span className="truncate">{selectedRepo.name}</span>
                                    </>
                                ) : (
                                    <span className="text-muted-foreground">Select repository</span>
                                )}
                            </div>
                            <ChevronDown className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        </button>

                        {/* Dropdown */}
                        {showRepoDropdown && (
                            <div className="absolute top-full left-0 right-0 mt-1 bg-popover border border-border rounded-lg shadow-lg z-50 overflow-hidden">
                                {repositories.length > 0 && (
                                    <div className="max-h-48 overflow-y-auto">
                                        {repositories.map((repo) => (
                                            <button
                                                key={repo.id}
                                                onClick={() => {
                                                    selectRepo(repo);
                                                    setShowRepoDropdown(false);
                                                }}
                                                className="w-full flex items-center gap-2 p-2 hover:bg-accent text-sm text-left"
                                            >
                                                {getStatusIcon(repo.status)}
                                                <span className="truncate">{repo.name}</span>
                                                {selectedRepo?.id === repo.id && (
                                                    <Check className="w-3 h-3 ml-auto text-primary" />
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                )}
                                <button
                                    onClick={() => {
                                        setShowRepoDropdown(false);
                                        setShowAddDialog(true);
                                    }}
                                    className="w-full flex items-center gap-2 p-2 hover:bg-accent text-sm border-t border-border text-primary"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add repository
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-3 space-y-1">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${isActive
                                        ? 'bg-primary/10 text-primary'
                                        : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                                    }`}
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="font-medium">{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer */}
                <div className="p-3 border-t border-border">
                    <div className="text-xs text-muted-foreground text-center">
                        CodeGraph v0.1.0
                    </div>
                </div>
            </aside>

            {/* Add Repository Dialog */}
            <AddRepoDialog open={showAddDialog} onOpenChange={setShowAddDialog} />
        </>
    );
}
