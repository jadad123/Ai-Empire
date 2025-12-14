import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    LayoutDashboard,
    Globe,
    Rss,
    FileText,
    Settings,
    Zap
} from 'lucide-react';

export default function Sidebar() {
    const { t } = useTranslation();

    const navItems = [
        { to: '/', icon: LayoutDashboard, label: t('nav.dashboard') },
        { to: '/sites', icon: Globe, label: t('nav.sites') },
        { to: '/sources', icon: Rss, label: t('nav.sources') },
        { to: '/articles', icon: FileText, label: t('nav.articles') },
        { to: '/settings', icon: Settings, label: t('nav.settings') },
    ];

    return (
        <aside className="sidebar w-64 min-h-screen p-4 fixed top-0 right-0 rtl:right-0 rtl:left-auto ltr:left-0 ltr:right-auto">
            {/* Logo */}
            <div className="flex items-center gap-3 px-4 py-6 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Zap className="w-6 h-6 text-white" />
                </div>
                <div>
                    <h1 className="font-bold text-lg gradient-text">{t('app.title')}</h1>
                    <p className="text-xs text-gray-500">AI Content Empire</p>
                </div>
            </div>

            {/* Navigation */}
            <nav className="space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                            `sidebar-link ${isActive ? 'active' : ''}`
                        }
                    >
                        <item.icon className="w-5 h-5" />
                        <span>{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Stats Summary */}
            <div className="mt-auto pt-6 border-t border-white/10 mt-8">
                <div className="glass-card-light p-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">الحالة</span>
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    </div>
                    <p className="text-xs text-gray-500">جميع الأنظمة تعمل بشكل طبيعي</p>
                </div>
            </div>
        </aside>
    );
}
