import { useTranslation } from 'react-i18next';
import { Bell, Search, Globe } from 'lucide-react';

export default function Header() {
    const { t, i18n } = useTranslation();

    const toggleLanguage = () => {
        const newLang = i18n.language === 'ar' ? 'en' : 'ar';
        i18n.changeLanguage(newLang);
    };

    return (
        <header className="glass-card px-6 py-4 mb-6 flex items-center justify-between">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
                <Search className="absolute right-3 rtl:right-3 ltr:left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    placeholder={t('common.search')}
                    className="input-field pr-10 rtl:pr-10 ltr:pl-10"
                />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
                {/* Language Toggle */}
                <button
                    onClick={toggleLanguage}
                    className="btn-secondary flex items-center gap-2 !py-2 !px-3"
                >
                    <Globe className="w-4 h-4" />
                    <span>{i18n.language === 'ar' ? 'EN' : 'عربي'}</span>
                </button>

                {/* Notifications */}
                <button className="relative p-2 rounded-lg hover:bg-white/10 transition-colors">
                    <Bell className="w-5 h-5 text-gray-400" />
                    <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-red-500"></span>
                </button>

                {/* User */}
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold">
                        م
                    </div>
                </div>
            </div>
        </header>
    );
}
