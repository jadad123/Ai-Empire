import { Routes, Route } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Sites from './pages/Sites';
import Sources from './pages/Sources';
import Articles from './pages/Articles';
import Settings from './pages/Settings';

function App() {
    const { i18n } = useTranslation();

    // Update document direction based on language
    const isRTL = i18n.language === 'ar';
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    document.documentElement.lang = i18n.language;

    return (
        <Layout>
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/sites" element={<Sites />} />
                <Route path="/sources" element={<Sources />} />
                <Route path="/articles" element={<Articles />} />
                <Route path="/settings" element={<Settings />} />
            </Routes>
        </Layout>
    );
}

export default App;
