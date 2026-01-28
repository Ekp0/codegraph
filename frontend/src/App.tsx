import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ChatView } from './components/ChatView';
import { GraphView } from './components/GraphView';
import { SettingsView } from './components/SettingsView';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Navigate to="/chat" replace />} />
                    <Route path="chat" element={<ChatView />} />
                    <Route path="graph" element={<GraphView />} />
                    <Route path="settings" element={<SettingsView />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

export default App;
